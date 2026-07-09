import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;

import com.google.gson.JsonObject;

import java.io.IOException;
import java.io.OutputStream;

import java.net.InetSocketAddress;
import java.net.URI;

import java.util.concurrent.Executors;

public class api {
    public static void main(String[] args) throws Exception {
        int port = 6767;

        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);

        server.setExecutor(Executors.newCachedThreadPool()); // for multi connections

        server.createContext("/", new PingHandler());
        server.start();
    }

    static class PingHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            if (!exchange.getRequestMethod().equals("GET")) {
                exchange.sendResponseHeaders(405, -1); // force only GET
                return;
            }

            try {
                URI uri = exchange.getRequestURI();
                String path = uri.getPath();

                if (path.startsWith("/")) {
                    path = path.substring(1);
                }

                if (path.isEmpty()) {
                    sendJsonResponse(exchange, 400, "{\"error\": \"Please provide a valid server address\"}");
                    return;
                }

                String host = "";
                int port = 25565;

                if (path.contains(":")) {
                    String[] parts = path.split(":", 2);
                    host = parts[0];
                    port = Integer.parseInt(parts[1]);
                }
                else {
                    host = path;
                }

                if (host.isEmpty() || port == -1) {
                    throw new Exception("Bad!");
                }

                InetSocketAddress resolved = resolveSRV.resolveSRV(host, port);
                JsonObject result = pingServers.ping(resolved.getHostString(), resolved.getPort(), 5000, 3);

                sendJsonResponse(exchange, 200, result.toString());
            }
            catch (NumberFormatException e) {
                sendJsonResponse(exchange, 400, "{\"error\": \"Invalid port format. Use /host:port\"}");
            }
            catch (Exception e) {
                e.printStackTrace();
                sendJsonResponse(exchange, 500, "{\"error\": \"Internal server error\"}");
            }
        }

        // send results back
        private void sendJsonResponse(HttpExchange exchange, int statusCode, String json) throws IOException {
            byte[] bytes = json.getBytes("UTF-8");

            exchange.getResponseHeaders().set("Content-Type", "application/json; charset=UTF-8");
            exchange.sendResponseHeaders(statusCode, bytes.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(bytes);
            }
            catch (Exception e) {
                System.out.println("hi");
            }
        }
    }
}
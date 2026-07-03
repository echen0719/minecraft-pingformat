import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.google.gson.JsonElement;

public class pingServers {
    public static byte[] encode(int value) {
        ByteArrayOutputStream result = new ByteArrayOutputStream(); // kind of like bytearray() in python

        while (true) {
            int b = value & 0x7F;
            value = value >> 7;

            if (value == 0) {
                result.write(b);
                return result.toByteArray();
            }

            result.write(b | 0x80);
        }

        return result.toByteArray();
    }

    // to store decoded values and indices
    static class decoded {
        int value;
        int index;

        decoded(int value, int index) {
            this.value = value;
            this.index = index;
        }
    }

    public static decoded decode(byte[] data, int i) throws IOException {
        int result = 0;
        int shift = 0;

        while (true) {
            int b = data[i];
            i++;
            result |= (b & 0x7F) << shift;

            if ((b & 0x80) == 0) {
                break;
            }

            shift += 7;
            if (shift > 35) {
                throw new IOException("VarInt too large");
            }
        }

        return new decoded(result, i);
    }

    public static int decodeReader(InputStream socket) throws IOException {
        int result = 0;
        int shift = 0;

        while (true) {
            int b = socket.read();

            if (b == -1) { // InputStream.read() return -1 at end of file
                throw new EOFException();
            }

            result |= (b & 0x7F) << shift;

            if ((b & 0x80) == 0)
                break;

            shift += 7;

            if (shift > 35) {
                throw new IOException("VarInt too large");
            }
        }

        return result;
    }

    // read and store into a byte array
    public static byte[] readPacket(InputStream socket) throws IOException {
        int length = decodeReader(socket);

        byte[] packet = new byte[length];
        int read = 0;

        while (read < length) {
            int data = socket.read(packet, read, length - read); // byte[], offset, length

            if (data == -1) {
                throw new EOFException();
            }

            read += data;
        }

        return packet;
    }

    // object so it could be string or int or etc...
    public Map<String, Object> ping(String host, int port, int timeout, int retries) {
        for (int attempt = 0; attempt < retries; attempt++) {
            Socket socket = new Socket();

            try {
                socket.connect(new InetSocketAddress(host, port));
                socket.setSoTimeout(timeout);

                InputStream reader = socket.getInputStream();
                OutputStream writer = socket.getOutputStream();

                int protocol = 67;
                byte[] bites = host.getBytes(StandardCharsets.UTF_8); // string -?> byte[]

                ByteArrayOutputStream handshakeStream = new ByteArrayOutputStream();

                handshakeStream.write(encode(0));
                handshakeStream.write(encode(protocol));
                handshakeStream.write(encode(bites.length));
                handshakeStream.write(bites);
                handshakeStream.write(ByteBuffer.allocate(2).putShort((short) port).array()); // struct.pack(">H", port) equivalent in Java
                handshakeStream.write(encode(1);

                byte[] handshake = handshakeStream.toByteArray();

                writer.write(encode(handshake.length));
                writer.write(handshake);
                writer.write(new byte[]{0x01, 0x00});
                writer.flush();

                byte[] packet = readPacket(reader);
                int packetID = packet[0];

                if (packetID != 0) {
                    throw new IOException("Unexpected packet id");
                }

                decoded result = decode(packet, 1);
                int length = result.value;
                int index = result.index;

                String response = new String(packet, index, length, StandardCharsets.UTF_8);

                JsonObject data = JsonParser.parseString(response).getAsJsonObject();
                JsonObject result = new JsonObject();

                result.addProperty("online", true);

                // reading docs be like...
                if (data.has("description")) {
                    JsonElement description = data.get("description");

                    if (description.has("text")) {
                        result.addProperty("motd", description.get("text").getAsString());
                    }
                }
                if (data.has("version") && data.get("version").isJsonObject()) {
                    JsonObject version = data.getAsJsonObject("version");

                    if (version.has("name")) {
                        result.addProperty("version", version.get("name").getAsString());
                    }

                    if (version.has("protocol")) {
                        result.addProperty("protocol", version.get("protocol").getAsInt());
                    }
                }
                if (data.has("players") && data.get("players").isJsonObject()) {
                    JsonObject players = data.getAsJsonObject("players");

                    if (players.has("online")) {
                        result.addProperty("online", version.get("online").getAsInt());
                    }

                    if (players.has("max")) {
                        result.addProperty("max", version.get("max").getAsInt());
                    }
                }

                return result;
            }

            catch (Exeception e) {
                System.out.println("Failed. Trying attempt (" + attempt + "/" + retries + ")...");
            }

            finally {
                if (socket != null && !socket.isClosed()) {
                    try {
                        socket.close();
                    }
                    catch (IOException) {}
                }
            }

            JsonObject offline = new JsonObject();
            offline.addProperty("online", false);
            return offline;
        }
    }

    public static void main(String[] args) {
    g
    }
}
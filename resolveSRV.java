import java.net.InetSocketAddress;

import javax.naming.Context;
import javax.naming.directory.Attributes;
import javax.naming.directory.DirContext;
import javax.naming.directory.InitialDirContext;
import javax.naming.NamingEnumeration;

import java.util.ArrayList;
import java.util.List;
import java.util.Hashtable;
import java.util.Comparator;

public class resolveSRV {
// just copied this https://stackoverflow.com/questions/78165993
    public static InetSocketAddress resolveSRV(String host, int port) {
        if (host.matches("^([0-9]{1,3}\\.){3}[0-9]{1,3}$")) { //abc.def.ghi.jkl format
            return new InetSocketAddress(host, port);
        }

        try {
            Hashtable<String, String> env = new Hashtable<>();
            env.put(Context.INITIAL_CONTEXT_FACTORY, "com.sun.jndi.dns.DnsContextFactory"); // default?
            DirContext ctx = new InitialDirContext(env);

            Attributes attrs = ctx.getAttributes("_minecraft._tcp." + host, new String[]{"SRV"});
            NamingEnumeration<?> enumeration = attrs.get("SRV").getAll();

            // from what I understand, the dns server responds with a list of ips with prediction chances

            List<String> records = new ArrayList<>();
            while (enumeration.hasMore()) {
                records.add((String) enumeration.next());
            }

            if (records.isEmpty()) {
                return new InetSocketAddress(host, port);
            }

            // https://github.com/xPaw/PHP-Minecraft-Query/blob/master/src/SRVResolver.php

            records.sort(Comparator.
                <String>comparingInt(r -> Integer.parseInt(r.split("\\s+")[0])). // lowest priority, highest weight
                thenComparing(r -> Integer.parseInt(r.split("\\s+")[1]), Comparator.reverseOrder())
            );

            String bestRecord = records.get(0);
            String[] parts = bestRecord.split("\\s+");

            if (parts.length >= 4) {
                int srvPort = Integer.parseInt(parts[2]);
                String target = parts[3];

                if (target.endsWith(".")) {
                    target = target.substring(0, target.length() - 1);
                }

                return new InetSocketAddress(target, srvPort);
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }

        return new InetSocketAddress(host, port);
    }
}
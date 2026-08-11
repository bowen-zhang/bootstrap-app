import { createClient } from "@connectrpc/connect";
import { createGrpcWebTransport } from "@connectrpc/connect-web";
import { GreetingService } from "../libs/api_pb";

const transport = createGrpcWebTransport({
  baseUrl: `${window.location.origin}/api`,
});

var greetingService: GreetingService | null = null;

export function getGreetingService() {
  if (greetingService === null) {
    greetingService = createClient(GreetingService, transport);
  }
  return greetingService;
}

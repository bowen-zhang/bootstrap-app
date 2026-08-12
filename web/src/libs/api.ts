import { createClient } from "@connectrpc/connect";
import { createGrpcWebTransport } from "@connectrpc/connect-web";
import { AccountService, GreetingService } from "../libs/api_pb";

const transport = createGrpcWebTransport({
  baseUrl: `${window.location.origin}/api`,
});

let greetingService: ReturnType<typeof createClient<typeof GreetingService>> | null = null;
let accountService: ReturnType<typeof createClient<typeof AccountService>> | null = null;

export function getGreetingService() {
  if (greetingService === null) {
    greetingService = createClient(GreetingService, transport);
  }
  return greetingService;
}

export function getAccountService() {
  if (accountService === null) {
    accountService = createClient(AccountService, transport);
  }
  return accountService;
}
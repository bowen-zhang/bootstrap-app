import { ConnectError, Code, createClient, type Interceptor } from "@connectrpc/connect";
import { createGrpcWebTransport } from "@connectrpc/connect-web";
import { AccountService, GreetingService } from "../libs/api_pb";
import { logout } from "@/libs/user";

let refreshPromise: Promise<void> | null = null;

async function refreshAccessToken() {
  if (refreshPromise) {
    await refreshPromise;
    return;
  }

  refreshPromise = getAccountService()
    .refreshToken({})
    .then(() => {
      console.log("Access token refreshed successfully");
    })
    .catch(async (error) => {
      console.log("Failed to refresh access token");
      logout();
      throw error;
    })
    .finally(() => {
      refreshPromise = null;
    });

  await refreshPromise;
}

const whitelist = new Set([
  "app.v1.AccountService/Create",
  "app.v1.AccountService/Login",
  "app.v1.AccountService/RefreshToken",
  "app.v1.AccountService/Logout",
]);

const authInterceptor: Interceptor = (next) => async (req) => {
  const requestPath = `${req.service.typeName}/${req.method.name}`;
  if (whitelist.has(requestPath)) {
    return await next(req);
  }

  try {
    return await next(req);
  } catch (error) {
    const connectErr = ConnectError.from(error);
    if (connectErr.code === Code.Unauthenticated) {
      await refreshAccessToken();
      return await next(req);
    }

    throw error;
  }
};

const transport = createGrpcWebTransport({
  baseUrl: `${window.location.origin}/api`,
  useBinaryFormat: false,
  interceptors: [authInterceptor],
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
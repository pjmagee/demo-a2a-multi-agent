export const BFF_BASE_URL =
  process.env.NEXT_PUBLIC_BFF_URL?.replace(/\/$/, "") ?? "http://localhost:8100/api";

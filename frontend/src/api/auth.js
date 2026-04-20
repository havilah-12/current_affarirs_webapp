import { api } from "./client.js";



export async function signup({ email, password }) {
  const { data } = await api.post("/auth/signup", { email, password });
  return data; // { access_token, token_type, expires_in }
}

export async function login({ email, password }) {
  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);

  const { data } = await api.post("/auth/login", body, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data; // { access_token, token_type, expires_in }
}

export async function fetchMe() {
  const { data } = await api.get("/auth/me");
  return data; // { id, email, created_at }
}

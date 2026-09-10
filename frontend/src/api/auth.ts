import { api } from "./client";
import type { Admin } from "../types/admin";

export async function login(username: string, password: string): Promise<Admin> {
  const res = await api.post<Admin>("/auth/login", { username, password });
  return res.data;
}

export async function logout(): Promise<void> {
  await api.post("/auth/logout");
}

export async function getCurrentAdmin(): Promise<Admin> {
  const res = await api.get<Admin>("/auth/me");
  return res.data;
}
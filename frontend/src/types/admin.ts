export interface Admin {
  id: number;
  username: string;
  email: string | null;
  is_active: boolean;
  last_login: string | null;
}
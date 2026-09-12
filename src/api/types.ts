export interface AdminOut {
  id: number;
  username: string;
  email: string | null;
  is_active: boolean;
  last_login: string | null;
}

export interface DeviceOut {
  id: number;
  name: string;
  device_type: string;
  status: "online" | "offline" | "warning" | "unknown";
  ip_address: string | null;
  site_name: string | null;
  backbone_name: string | null;
}

export interface GNS3Project {
  project_id: string;
  name: string;
  status: string;
}

export interface ImportResult {
  project: string;
  devices_created: number;
  devices_updated: number;
  links_created: number;
  links_updated: number;
  unmatched_site_warning: string[];
}

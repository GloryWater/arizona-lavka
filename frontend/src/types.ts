// ============================================================================
// AUTH TYPES
// ============================================================================

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  is_premium: boolean;
  is_telegram_user: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

export interface LoginData {
  username_or_email: string;
  password: string;
}

// ============================================================================
// MARKETPLACE TYPES
// ============================================================================

export interface Offer {
  type: 'sell' | 'buy';
  itemId: number;
  itemName: string;
  price: number;
  count: number;
  username: string;
  lavkaUid: string;
  serverId: number;
  serverName: string;
  userStatus: boolean;
}

export interface OffersResponse {
  offers: Offer[];
  total: number;
  servers: number;
}

export interface Server {
  id: number;
  name: string;
}

export interface ServersResponse {
  servers: Server[];
  total: number;
}

export interface Lavka {
  lavkaUid: string;
  username: string;
  serverId: number;
  serverName: string;
  sellCount: number;
  buyCount: number;
  totalItems: number;
}

export interface LavkasResponse {
  lavkas: Lavka[];
  total: number;
  serverName: string;
}

export interface LavkaItem {
  itemId: number;
  itemName: string;
  price: number;
  count: number;
  type: 'sell' | 'buy';
}

export interface LavkaDetail {
  lavkaUid: string;
  username: string;
  serverId: number;
  serverName: string;
  userStatus: boolean;
  sellItems: LavkaItem[];
  buyItems: LavkaItem[];
  totalSell: number;
  totalBuy: number;
}

export interface ItemsMapping {
  [key: string]: string;
}

// ============================================================================
// CONFIG TYPES
// ============================================================================

export type ConfigMode = 'SELL' | 'BUY';

export interface ConfigGenerateRequest {
  server_id: number;
  mode: ConfigMode;
  percentage: number;
  save_to_history?: boolean;
}

export interface ConfigItem {
  price: string;
  maximum: boolean;
  enabled: boolean;
  name: string;
  price_vc: number;
  count: number;
  slot_count: string[];
  slot_id: string[];
  position_tab: number;
  all_count: number;
  continue: string;
  count_maximum: number;
}

export interface ConfigHistoryItem {
  id: number;
  server_name: string;
  server_id: number;
  mode: ConfigMode;
  percentage: number;
  items_count: number;
  created_at: string;
  download_count: number;
}

// Backend возвращает просто массив, не объект с configs
export type ConfigHistoryResponse = ConfigHistoryItem[];

// ============================================================================
// USER TYPES
// ============================================================================

export interface UserProfile extends User {
  configs_count: number;
}

export interface FavoriteItem {
  id: number;
  item_id: number;
  item_name: string;
  target_price: number | null;
  target_percentage: number;
  mode: ConfigMode;
  server_id: number;
  notes: string | null;
  is_active: boolean;
  created_at: string;
}

export interface PriceAlert {
  id: number;
  item_id: number;
  item_name: string;
  server_id: number;
  target_price: number;
  condition: 'above' | 'below';
  is_active: boolean;
  triggered: boolean;
  triggered_at: string | null;
  triggered_price: number | null;
  created_at: string;
}

// ============================================================================
// API TYPES
// ============================================================================

export interface ApiError {
  detail: string;
  status_code?: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page?: number;
  limit?: number;
}

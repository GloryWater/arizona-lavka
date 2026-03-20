// ============================================================================
// ОБЩИЕ ТИПЫ
// ============================================================================

export interface ApiError {
  detail: string;
  status_code?: number;
  code?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page?: number;
  limit?: number;
}

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
  role: 'user' | 'admin';
  last_active_at: string | null;
  created_at: string;
}

export interface UserProfile extends User {
  configs_count: number;
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
  turnstile_token: string;  // Cloudflare Turnstile verification token
}

export interface LoginData {
  username_or_email: string;
  password: string;
}

export interface TelegramLoginData {
  init_data: string;
}

// ============================================================================
// MARKETPLACE TYPES
// ============================================================================

export type OfferType = 'sell' | 'buy';

export interface Offer {
  type: OfferType;
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

export interface SearchResults {
  buy_offers: Offer[];
  sell_offers: Offer[];
  total_buy: number;
  total_sell: number;
  limit: number;
  offset: number;
  server_id: number | null;
  search_term: string;
  sort_order: string;
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
  type: OfferType;
}

export interface LavkaDetail {
  lavkaUid: string;
  username: string;
  serverId: number;
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

export type ConfigGenerationType = 'all' | 'liquidity' | 'category';

export interface ConfigGenerateRequest {
  server_id: number;
  mode: ConfigMode;
  percentage: number;
  min_liquidity?: number;
  save_to_history?: boolean;
}

export interface ConfigItemResponse {
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
  continue_: string;
  count_maximum: number;
}

export interface ConfigStatsResponse {
  total_items: number;
  items_with_history: number;
  avg_confidence: number;
  price_range: Record<string, unknown>;
}

export interface ConfigGenerateResponse {
  config: ConfigItemResponse[];
  total_items: number;
  server_name: string;
  mode: string;
  stats: ConfigStatsResponse;
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

export type ConfigHistoryResponse = ConfigHistoryItem[];

export interface Category {
  key: string;
  name: string;
}

export interface CategoriesResponse {
  categories: Category[];
}

// ============================================================================
// USER TYPES
// ============================================================================

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

export interface FavoriteItemCreate {
  item_id: number;
  item_name: string;
  target_price?: number;
  target_percentage: number;
  mode: ConfigMode;
  server_id: number;
  notes?: string;
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

export interface PriceAlertCreate {
  item_id: number;
  item_name: string;
  server_id: number;
  target_price: number;
  condition: 'above' | 'below';
}

// ============================================================================
// ADMIN TYPES
// ============================================================================

export interface AdminUser extends User {
  configs_count: number;
}

export interface AdminLog {
  id: number;
  user_id: number | null;
  username: string | null;
  event_type: string;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

export interface AuditLog {
  id: number;
  user_id: number | null;
  username: string | null;
  action: string;
  resource: string | null;
  resource_id: number | null;
  ip_address: string | null;
  details: string | null;
  status: string;
  error_message: string | null;
  created_at: string;
}

export interface AdminStatsSummary {
  total_users: number;
  total_configs: number;
  dau: number;
  mau: number;
  avg_configs_per_user_per_day: number;
}

export interface AdminStatsChartData {
  date: string;
  registrations: number;
  configs_generated: number;
}

export interface GlobalSetting {
  key: string;
  value: Record<string, unknown>;
  updated_at: string;
}

export interface GlobalSettingUpdate {
  value: Record<string, unknown>;
}

export interface MaintenanceStatus {
  enabled: boolean;
  info: {
    enabled: boolean;
    message?: string;
    estimated_end?: string;
  } | null;
}

export type AdminLogEventType =
  | 'login'
  | 'logout'
  | 'user_created'
  | 'user_updated'
  | 'user_deleted'
  | 'config_generated'
  | 'settings_updated'
  | 'export_data'
  | 'view_logs'
  | 'view_stats';

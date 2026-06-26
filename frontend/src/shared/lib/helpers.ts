export function formatNumber(value: number) {
  return new Intl.NumberFormat('ru-RU').format(value);
}

export function formatPrice(value: number, serverId?: number) {
  const formatted = formatNumber(value);
  return serverId === 0 ? `${formatted} VC` : `$${formatted}`;
}

export function formatDate(value: string | number | Date) {
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}

// Константы для приложения

export const SERVERS = [
  { id: -1, name: 'Все сервера' },
  { id: 0, name: 'Arizona 1' },
  { id: 1, name: 'Arizona 2' },
  { id: 2, name: 'Arizona 3' },
  { id: 3, name: 'Arizona 4' },
  { id: 4, name: 'Arizona 5' },
  { id: 5, name: 'Arizona 6' },
  { id: 6, name: 'Arizona 7' },
  { id: 7, name: 'Arizona 8' },
  { id: 8, name: 'Arizona 9' },
  { id: 9, name: 'Arizona 10' },
  { id: 10, name: 'Arizona 11' },
  { id: 11, name: 'Arizona 12' },
  { id: 12, name: 'Arizona 13' },
  { id: 13, name: 'Arizona 14' },
  { id: 14, name: 'Arizona 15' },
  { id: 15, name: 'Arizona 16' },
  { id: 16, name: 'Arizona 17' },
  { id: 17, name: 'Arizona 18' },
  { id: 18, name: 'Arizona 19' },
  { id: 19, name: 'Arizona 20' },
  { id: 20, name: 'Arizona 21' },
  { id: 21, name: 'Arizona 22' },
  { id: 22, name: 'Arizona 23' },
  { id: 23, name: 'Arizona 24' },
  { id: 24, name: 'Arizona 25' },
  { id: 25, name: 'Arizona 26' },
  { id: 26, name: 'Arizona 27' },
  { id: 27, name: 'Arizona 28' },
  { id: 28, name: 'Arizona 29' },
  { id: 29, name: 'Arizona 30' },
  { id: 30, name: 'Arizona 31' },
  { id: 31, name: 'Arizona 32' },
  { id: 32, name: 'Arizona 33' },
];

export const SORT_OPTIONS = [
  { value: 'none', label: 'Без сортировки' },
  { value: 'asc', label: 'По возрастанию' },
  { value: 'desc', label: 'По убыванию' },
];

export const MODE_OPTIONS = [
  { value: 'SELL', label: 'Продажа' },
  { value: 'BUY', label: 'Покупка' },
];

export const formatPrice = (price: number): string => {
  return new Intl.NumberFormat('ru-RU').format(price);
};

export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
};

export const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) {
    return 'Сегодня';
  } else if (days === 1) {
    return 'Вчера';
  } else if (days < 7) {
    return `${days} дн. назад`;
  } else {
    return formatDate(dateString);
  }
};

// Константы для приложения

export const SERVERS = [
  { id: 0, name: 'Vice City' },
  { id: 1, name: 'Phoenix' },
  { id: 2, name: 'Tucson' },
  { id: 3, name: 'Scottsdale' },
  { id: 4, name: 'Chandler' },
  { id: 5, name: 'Brainburg' },
  { id: 6, name: 'Saint Rose' },
  { id: 7, name: 'Mesa' },
  { id: 8, name: 'Red Rock' },
  { id: 9, name: 'Yuma' },
  { id: 10, name: 'Surprise' },
  { id: 11, name: 'Prescott' },
  { id: 12, name: 'Glendale' },
  { id: 13, name: 'Kingman' },
  { id: 14, name: 'Winslow' },
  { id: 15, name: 'Payson' },
  { id: 16, name: 'Gilbert' },
  { id: 17, name: 'Show Low' },
  { id: 18, name: 'Casa Grande' },
  { id: 19, name: 'Page' },
  { id: 20, name: 'Sun City' },
  { id: 21, name: 'Queen Creek' },
  { id: 22, name: 'Sedona' },
  { id: 23, name: 'Holiday' },
  { id: 24, name: 'Wednesday' },
  { id: 25, name: 'Yava' },
  { id: 26, name: 'Faraway' },
  { id: 27, name: 'Bumble Bee' },
  { id: 28, name: 'Christmas' },
  { id: 29, name: 'Mirage' },
  { id: 30, name: 'Love' },
  { id: 31, name: 'Drake' },
  { id: 32, name: 'Space' },
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

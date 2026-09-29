export const PHONE_HINT = 'enter valid ph. no.';

export function digitsOnly(value: string): string {
  return (value || '').replace(/\D/g, '').slice(0, 10);
}

export function validIndianMobile(value: string): boolean {
  if (!/^[6-9]\d{9}$/.test(value || '')) return false;
  const number = Number(value);
  return number >= 6000000000 && number <= 9999999999;
}

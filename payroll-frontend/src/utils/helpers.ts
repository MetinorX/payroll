import { CURRENCY_SYMBOL } from './constants';

export function formatCurrency(amount: number): string {
  return `${CURRENCY_SYMBOL}${amount?.toLocaleString('en-IN') ?? 0}`;
}

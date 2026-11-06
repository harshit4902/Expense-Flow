export const formatRupees = (paise) => {
  if (paise === null || paise === undefined) return '₹0.00';
  const rupees = paise / 100.0;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(rupees);
};

export const rupeesToPaise = (rupees) => {
  if (!rupees || isNaN(rupees)) return 0;
  return Math.round(parseFloat(rupees) * 100);
};

export const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
};


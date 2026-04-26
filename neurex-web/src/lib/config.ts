export const API_BASE = window.location.origin.includes(":3000") 
  ? window.location.origin.replace(":3000", ":8000") 
  : window.location.origin;

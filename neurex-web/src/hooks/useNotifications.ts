import { useEffect } from 'react';

const VAPID_PUBLIC_KEY = 'BPXD9z076zxWXfa8rDgeEF4l6N240ChuS1TivvgPzLEOovAyX-2rwuTE0fYav6Z7UMmlx-97k3H8et5yFtH5giI';
const API_BASE = 'http://127.0.0.1:8000';

export function useNotifications() {
  useEffect(() => {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      return;
    }

    async function subscribe() {
      try {
        const registration = await navigator.serviceWorker.ready;
        
        // Check if already subscribed
        let subscription = await registration.pushManager.getSubscription();
        
        if (!subscription) {
          // Request permission
          const permission = await Notification.requestPermission();
          if (permission !== 'granted') return;

          subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
          });
        }

        // Send to backend
        await fetch(`${API_BASE}/api/notifications/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(subscription)
        });
        
        console.log('Push notification registered');
      } catch (err) {
        console.error('Push subscription failed', err);
      }
    }

    subscribe();
  }, []);
}

function urlBase64ToUint8Array(base64String: string) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/\-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

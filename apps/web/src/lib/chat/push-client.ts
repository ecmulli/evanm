import { getVapidKey, subscribePush } from './api';

function urlBase64ToUint8Array(base64: string): Uint8Array {
  const padding = '='.repeat((4 - (base64.length % 4)) % 4);
  const b64 = (base64 + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(b64);
  return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)));
}

// Registers the SW, requests permission, subscribes to push, and stores the
// subscription on the bridge (keyed by profile). On iOS this only works once the
// PWA is installed to the home screen and served over HTTPS.
export async function enablePush(profileId: string): Promise<void> {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    alert('Push not supported here. On iPhone: add to Home Screen first, then enable.');
    return;
  }
  const perm = await Notification.requestPermission();
  if (perm !== 'granted') { alert('Notifications were not allowed.'); return; }

  const reg = await navigator.serviceWorker.register('/sw.js');
  await navigator.serviceWorker.ready;

  const { key } = await getVapidKey();
  if (!key) {
    alert('Server push not configured yet (needs VAPID keys + a public HTTPS origin via Funnel).');
    return;
  }
  const sub = await reg.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(key) as BufferSource,
  });
  await subscribePush(profileId, sub.toJSON() as PushSubscriptionJSON);
  alert('Notifications enabled.');
}

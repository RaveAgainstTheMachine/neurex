// neurex-web/src/lib/lsp.ts
import { listen } from 'vscode-ws-jsonrpc';
import {
    MonacoLanguageClient,
    MessageConnection,
    CloseAction,
    ErrorAction
} from 'monaco-languageclient';
import { initServices } from 'monaco-languageclient/vscodeApiWrapper';
import { API_BASE } from './config';

let servicesInitialized = false;

export async function createLSPConnection(lang: string, token: string): Promise<MonacoLanguageClient> {
    if (!servicesInitialized) {
        await initServices({
            userServices: {
                // Add specific VSCode services here if needed
            },
            debugLogging: true
        });
        servicesInitialized = true;
    }

    const wsUrl = `${window.location.origin.replace('http', 'ws')}/api/websocket/ws/lsp/${lang}?token=${token}`;
    const webSocket = new WebSocket(wsUrl);

    return new Promise((resolve, reject) => {
        webSocket.onopen = () => {
            const socket = {
                send: (content: string) => webSocket.send(content),
                onMessage: (cb: (data: any) => void) => {
                    webSocket.onmessage = (event) => cb(event.data);
                },
                onError: (cb: (err: any) => void) => {
                    webSocket.onerror = (event) => cb(event);
                },
                onClose: (cb: (code: number, reason: string) => void) => {
                    webSocket.onclose = (event) => cb(event.code, event.reason);
                },
                dispose: () => webSocket.close()
            };

            listen({
                webSocket: socket as any,
                onConnection: (connection: MessageConnection) => {
                    const languageClient = new MonacoLanguageClient({
                        name: `${lang.toUpperCase()} Language Client`,
                        clientOptions: {
                            documentSelector: [lang],
                            errorHandler: {
                                error: () => ErrorAction.Continue,
                                closed: () => CloseAction.DoNotRestart
                            }
                        },
                        connectionProvider: {
                            get: () => Promise.resolve(connection)
                        }
                    });
                    languageClient.start();
                    console.log(`LSP started for ${lang}`);
                    resolve(languageClient);
                }
            });
        };
        webSocket.onerror = (err) => reject(err);
    });
}

class LSPManager {
    private clients: Map<string, MonacoLanguageClient> = new Map();

    async connect(lang: string, token: string) {
        if (this.clients.has(lang)) return;
        
        try {
            const client = await createLSPConnection(lang, token);
            this.clients.set(lang, client);
        } catch (err) {
            console.error(`Failed to connect LSP for ${lang}`, err);
        }
    }

    dispose(lang: string) {
        const client = this.clients.get(lang);
        if (client) {
            client.stop();
            this.clients.delete(lang);
        }
    }

    disposeAll() {
        this.clients.forEach(c => c.stop());
        this.clients.clear();
    }
}

export const lspManager = new LSPManager();

export async function installLanguageServer(lang: string, token: string) {
    const res = await fetch(`${API_BASE}/api/languages/install/${lang}`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Installation failed");
    }
    return res.json();
}

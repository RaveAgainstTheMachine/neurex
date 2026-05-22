import { WebSocketMessageReader, WebSocketMessageWriter } from 'vscode-ws-jsonrpc';
import {
    MonacoLanguageClient,
} from 'monaco-languageclient';
import { MonacoVscodeApiWrapper } from 'monaco-languageclient/vscodeApiWrapper';
import { _API_BASE } from './config';
import { api } from './api';
import { useStore } from './store';

let servicesInitialized = false;

export async function createLSPConnection(lang: string, _token: string): Promise<MonacoLanguageClient> {
    if (!servicesInitialized) {
        const wrapper = new MonacoVscodeApiWrapper({
            $type: 'classic',
            viewsConfig: {
                $type: 'EditorService'
            },
            serviceOverrides: {
                // Add overrides if needed
            },
            logLevel: 1 // Info
        });
        await wrapper.start();
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

            const messageTransports = {
                reader: new WebSocketMessageReader(socket as any),
                writer: new WebSocketMessageWriter(socket as any)
            };

            const languageClient = new MonacoLanguageClient({
                name: `${lang.toUpperCase()} Language Client`,
                clientOptions: {
                    documentSelector: [lang],
                    errorHandler: {
                        error: () => ({ action: 1 }), // ErrorAction.Continue
                        closed: () => ({ action: 1 }) // CloseAction.DoNotRestart
                    }
                },
                messageTransports
            });

            languageClient.onNotification('textDocument/publishDiagnostics', (params: any) => {
                const uri = params.uri;
                let path = uri.replace('file://', '');
                const wsPath = window.localStorage.getItem('workspace_path') || '';
                if (path.startsWith(wsPath)) {
                    path = path.substring(wsPath.length).replace(/^\//, '');
                }
                useStore.getState().updateDiagnostics(path, params.diagnostics);
            });

            languageClient.start();
            console.log(`LSP started for ${lang}`);
            resolve(languageClient);
        };
        webSocket.onerror = (err) => reject(err);
    });
}

class LSPManager {
    private clients: Map<string, MonacoLanguageClient> = new Map();

    async connect(lang: string, _token: string) {
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

export async function installLanguageServer(lang: string, _token: string) {
    try {
        return await api.post(`/api/languages/install/${lang}`);
    } catch (_err: unknown) {
        throw new Error(err.message || "Installation failed");
    }
}

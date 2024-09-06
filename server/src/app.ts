import express from "express";
import expressWs from 'express-ws';
import WebSocket from 'ws';
import { createStore } from "redux";
import { rootReducer } from "./features";
import { connectedDevicesStateSlice } from "./features/connectedDevices";
import path from "path";
import crypt from "crypto";
import { loadFromFile, saveToFile } from "./backup";

const { app, getWss } = expressWs(express());

const store = createStore(rootReducer, loadFromFile("./save"));

app.ws('/ws', (ws, req) => {
    const wss = getWss();
    const sessionId = crypt.randomUUID();
    console.log(`connected (sid: ${sessionId})`);

    // 初回接続したクライアントに、現在の試合状況を送信する
    ws.send(JSON.stringify({
        type: 'welcome',
        sid: sessionId,
        time: Date.now(),
        state: store.getState(),
    }));

    // クライアントから送られたdispatchの処理
    ws.on('message', async (message) => {
        const body = JSON.parse(message.toString());
        const type = body?.type;
        console.log(`on message: `, body);

        if (type === "dispatch" || type === "dispatch_all") {
            const actions = body?.actions;

            actions.forEach((action) => {
                store.dispatch(action);
            });
            wss.clients.forEach(client => {
                if (client.readyState === WebSocket.OPEN) {
                    client.send(message.toString());
                }
            });
        }
        if (type === "save_store") {
            await saveToFile("./save", store);
        }
    });

    // 切断
    ws.on('close', (code, reason) => {
        console.log(`disconnect (sid: ${sessionId}): ${code} ${reason}`);

        const action = connectedDevicesStateSlice.actions.removeDevice({
            sockId: sessionId,
        });
        store.dispatch(action);
        wss.clients.forEach(client => {
            if (client.readyState === WebSocket.OPEN) {
                client.send(JSON.stringify([action]));
            }
        });
    });
});

// クライアントのホスティング
app.use(express.static("../client/dist"));
app.get("*", (req, res, next) => {
    res.sendFile(path.resolve("../client/dist/index.html"));
});

app.listen(8000);
console.log("server start");

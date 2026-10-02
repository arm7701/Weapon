import sys
import os
import json
import math
import urllib.request
import http.server
import socketserver
import threading
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLabel, QLineEdit, QPushButton, QComboBox, QTabWidget,
    QListWidget, QListWidgetItem, QDialog, QCheckBox, QRadioButton,
    QButtonGroup, QSpinBox, QFileDialog, QMessageBox, QGroupBox, QColorDialog,
    QFrame
)
from PySide6.QtGui import QColor
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QSize, Qt

# =========================================================================
# 1. HTML/JavaScript — Interactive 3D Edit Mode Engine with CesiumJS
#    ระบบ Edit Mode สำหรับวาด ปรับขนาด สร้าง/แก้ไข/ลบ วัตถุ 3D บนแผนที่
# =========================================================================
HTML_MAP_CODE_3D = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>CESIUM_EDIT_MODE</title>
    <script src="https://cesium.com/downloads/cesiumjs/releases/1.118/Build/Cesium/Cesium.js"></script>
    <link href="https://cesium.com/downloads/cesiumjs/releases/1.118/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { overflow: hidden; background: #000; font-family: 'Consolas', 'Courier New', monospace; }
        #cesiumContainer { width: 100vw; height: 100vh; }

        /* ===== Edit Toolbar (top bar) ===== */
        #editToolbar {
            position: absolute; top: 0; left: 0; right: 0; z-index: 9999;
            height: 52px;
            background: rgba(8, 12, 10, 0.92);
            border-bottom: 1px solid rgba(0, 255, 102, 0.3);
            backdrop-filter: blur(10px);
            display: flex; align-items: center; gap: 8px;
            padding: 0 12px;
        }
        .tb-btn {
            background: rgba(0, 120, 60, 0.7); color: #E0FFE8;
            border: 1px solid rgba(0, 200, 100, 0.5);
            padding: 7px 14px; border-radius: 5px;
            font-family: inherit; font-size: 11px; font-weight: bold;
            cursor: pointer; transition: all 0.2s; white-space: nowrap;
        }
        .tb-btn:hover { background: #00CC66; color: #000; box-shadow: 0 0 12px rgba(0,255,102,0.5); }
        .tb-btn.active { background: #00FF66; color: #000; box-shadow: 0 0 18px rgba(0,255,102,0.7); }
        .tb-btn.danger { background: rgba(160,20,20,0.7); border-color: #FF4444; color: #FFD0D0; }
        .tb-btn.danger:hover { background: #FF3333; color: #FFF; box-shadow: 0 0 12px rgba(255,50,50,0.6); }
        .tb-sel {
            background: #020604; color: #00FF66;
            border: 1px solid rgba(0,170,85,0.5); border-radius: 4px;
            padding: 6px 10px; font-family: inherit; font-size: 11px;
            cursor: pointer; outline: none;
        }
        .tb-inp {
            background: #020604; color: #38BDF8;
            border: 1px solid rgba(0,170,85,0.5); border-radius: 4px;
            padding: 6px 10px; font-family: inherit; font-size: 11px;
            width: 100px; outline: none;
        }
        .tb-inp:focus, .tb-sel:focus { border-color: #00FF66; box-shadow: 0 0 8px rgba(0,255,102,0.4); }
        .tb-sep { width: 1px; height: 28px; background: rgba(0,255,102,0.2); margin: 0 4px; }

        /* ===== Object Data Panel (right sidebar) ===== */
        #objectPanel {
            position: absolute; top: 52px; right: 0; bottom: 0;
            width: 330px; z-index: 9998;
            background: rgba(6, 10, 8, 0.94);
            border-left: 1px solid rgba(0, 255, 102, 0.3);
            backdrop-filter: blur(12px);
            display: none; flex-direction: column;
        }
        #objectPanel.visible { display: flex; animation: panelIn 0.35s ease; }
        @keyframes panelIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .pnl-hdr {
            padding: 12px 14px; display: flex; justify-content: space-between; align-items: center;
            border-bottom: 1px solid rgba(0,255,102,0.2);
            color: #00FF66; font-size: 12px; font-weight: bold; letter-spacing: 0.5px;
        }
        .pnl-cnt {
            background: rgba(0,255,102,0.15); color: #00FF66;
            padding: 2px 10px; border-radius: 10px; font-size: 11px;
        }
        #objList { flex: 1; overflow-y: auto; padding: 6px 0; }
        #objList::-webkit-scrollbar { width: 5px; }
        #objList::-webkit-scrollbar-track { background: transparent; }
        #objList::-webkit-scrollbar-thumb { background: rgba(0,255,102,0.3); border-radius: 3px; }

        .empty-st {
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            height: 200px; color: rgba(0,255,102,0.4); gap: 10px; font-size: 12px;
        }
        .empty-st .ico { font-size: 40px; opacity: 0.5; }

        /* ===== Object Cards ===== */
        .ocard {
            margin: 4px 8px; padding: 10px 12px;
            background: rgba(0, 35, 18, 0.6);
            border: 1px solid rgba(0,170,85,0.3);
            border-radius: 6px; cursor: pointer;
            transition: all 0.2s;
        }
        .ocard:hover { border-color: rgba(0,255,102,0.6); background: rgba(0,50,25,0.7); }
        .ocard.sel {
            border-color: #00FF66; background: rgba(0,70,35,0.7);
            box-shadow: 0 0 14px rgba(0,255,102,0.2);
        }
        .ctop { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
        .cname { color: #E0FFE8; font-size: 12px; font-weight: bold; }
        .ctype { color: #00CC66; font-size: 10px; background: rgba(0,200,100,0.1); padding: 2px 7px; border-radius: 3px; }
        .cinfo { color: #6B9080; font-size: 10px; line-height: 1.7; }
        .cbtns { display: flex; gap: 5px; margin-top: 8px; }
        .cbtn {
            flex: 1; padding: 5px 0; text-align: center;
            background: rgba(0,120,60,0.4); color: #A8FFB8;
            border: 1px solid rgba(0,170,85,0.3); border-radius: 4px;
            font-family: inherit; font-size: 10px; cursor: pointer; transition: all 0.15s;
        }
        .cbtn:hover { background: rgba(0,200,100,0.5); border-color: #00FF66; }
        .cbtn.del { background: rgba(120,20,20,0.4); color: #FFAAAA; border-color: rgba(200,50,50,0.3); }
        .cbtn.del:hover { background: rgba(200,30,30,0.5); border-color: #FF4444; }

        /* ===== Inline Edit Form ===== */
        .eform { display: none; margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(0,255,102,0.15); }
        .eform.vis { display: block; }
        .erow { display: flex; align-items: center; gap: 6px; margin-bottom: 5px; }
        .elbl { color: #6B9080; font-size: 10px; width: 55px; text-align: right; }
        .einp {
            flex: 1; background: #020604; color: #38BDF8;
            border: 1px solid rgba(0,170,85,0.4); border-radius: 3px;
            padding: 4px 7px; font-family: inherit; font-size: 11px; outline: none;
        }
        .einp:focus { border-color: #00FF66; box-shadow: 0 0 6px rgba(0,255,102,0.3); }
        .eacts { display: flex; gap: 5px; margin-top: 6px; }
        .eok {
            flex: 1; padding: 5px; text-align: center;
            background: #00AA55; color: #000; border: none; border-radius: 4px;
            font-family: inherit; font-size: 10px; font-weight: bold; cursor: pointer;
        }
        .eok:hover { background: #00FF66; }
        .ecc {
            flex: 1; padding: 5px; text-align: center;
            background: rgba(80,80,80,0.5); color: #AAA; border: 1px solid rgba(100,100,100,0.3);
            border-radius: 4px; font-family: inherit; font-size: 10px; cursor: pointer;
        }
        .ecc:hover { background: rgba(120,120,120,0.5); }

        /* ===== Drawing Guide (bottom center) ===== */
        #drawGuide {
            position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
            z-index: 9999; display: none;
            background: rgba(0,0,0,0.85); color: #00FF66;
            padding: 10px 22px; border-radius: 8px;
            border: 1px solid rgba(0,255,102,0.3);
            font-size: 12px; white-space: nowrap;
            backdrop-filter: blur(8px);
            animation: gGlow 1.5s ease-in-out infinite alternate;
        }
        @keyframes gGlow {
            from { box-shadow: 0 0 8px rgba(0,255,102,0.2); }
            to { box-shadow: 0 0 18px rgba(0,255,102,0.5); }
        }

        /* ===== Tactical Pin UI ===== */
        #controlPanel { position: absolute; top: 65px; left: 15px; z-index: 9999; }
        .tactical-btn {
            background: rgba(139, 0, 0, 0.8); color: #FFF; border: 2px solid #FF3333; padding: 8px 16px;
            font-family: 'Consolas', monospace; font-size: 12px; font-weight: bold;
            cursor: pointer; border-radius: 4px; box-shadow: 0 0 10px rgba(255,51,51,0.4); transition: all 0.2s;
        }
        .tactical-btn:hover { background: #FF3333; box-shadow: 0 0 15px rgba(255,51,51,0.8); }

        /* ===== Minimap 2D ===== */
        #minimapContainer {
            position: absolute; top: 65px; right: 15px; width: 150px; height: 150px;
            border: 2px solid rgba(0, 255, 102, 0.5); border-radius: 8px; z-index: 9998;
            background: #000; box-shadow: 0 0 15px rgba(0,0,0,0.8); overflow: hidden;
        }

        #objectPanel { display: none !important; }

        /* ===== Floating Image Draft Control Bar ===== */
        #imageControlBar {
            position: absolute; bottom: 25px; left: 50%; transform: translateX(-50%);
            background: rgba(2, 6, 4, 0.95); border: 2px solid #00AA55; border-radius: 8px;
            padding: 8px 16px; display: none; align-items: center; gap: 10px;
            box-shadow: 0 4px 25px rgba(0,0,0,0.9), 0 0 15px rgba(0,255,102,0.3);
            z-index: 10000; font-family: 'Consolas', monospace; font-size: 11px; color: #A8FFB8;
        }
        .icb-title { font-weight: bold; color: #00FF66; font-size: 12px; white-space: nowrap; margin-right: 4px; }
        .icb-group { display: flex; align-items: center; gap: 5px; white-space: nowrap; }
        .icb-group label { color: #6B9080; font-size: 10px; }
        .icb-group input[type=range] { width: 75px; accent-color: #00FF66; cursor: pointer; }
        .icb-btn {
            background: rgba(0,170,85,0.3); border: 1px solid rgba(0,255,102,0.4);
            color: #E0FFE8; padding: 4px 8px; border-radius: 4px; cursor: pointer;
            font-family: inherit; font-size: 11px; font-weight: bold; transition: all 0.15s;
        }
        .icb-btn:hover { background: #00FF66; color: #000; }
        .icb-btn.lock { background: rgba(0,100,200,0.4); border-color: #38BDF8; color: #38BDF8; }
        .icb-btn.lock.locked { background: #EAB308; border-color: #FACC15; color: #000; font-weight: bold; }
        .icb-btn.del { background: rgba(200,30,30,0.4); border-color: #FF4444; color: #FFAAAA; }
        .icb-btn.del:hover { background: #FF4444; color: #FFF; }
        .icb-btn.close { background: transparent; border: none; color: #6B9080; font-size: 14px; padding: 2px 6px; }
        .icb-btn.close:hover { color: #FF4444; }

        /* ===== Floating 3D Object Control Bar ===== */
        #objectControlBar {
            position: absolute; bottom: 25px; left: 50%; transform: translateX(-50%);
            background: rgba(4, 10, 15, 0.95); border: 2px solid #38BDF8; border-radius: 8px;
            padding: 8px 16px; display: none; align-items: center; gap: 10px;
            box-shadow: 0 4px 25px rgba(0,0,0,0.9), 0 0 15px rgba(56,189,248,0.3);
            z-index: 10000; font-family: 'Consolas', monospace; font-size: 11px; color: #E0FFE8;
        }
        .ocb-title { font-weight: bold; color: #38BDF8; font-size: 12px; white-space: nowrap; margin-right: 4px; }
        .ocb-group { display: flex; align-items: center; gap: 5px; white-space: nowrap; }
        .ocb-inp {
            background: #020604; color: #00FF66;
            border: 1px solid rgba(0, 255, 102, 0.5); border-radius: 4px;
            padding: 3px 5px; font-family: inherit; font-size: 11px; font-weight: bold;
            text-align: right; width: 55px; outline: none;
            transition: all 0.2s;
        }
        .ocb-inp:focus {
            border-color: #00FF66;
            box-shadow: 0 0 8px rgba(0, 255, 102, 0.6);
            background: #05150a;
        }
        .ocb-inp::-webkit-inner-spin-button, 
        .ocb-inp::-webkit-outer-spin-button { 
            opacity: 0.7;
        }
        .clr-dot {
            width: 17px; height: 17px; border-radius: 50%; border: 1.5px solid rgba(255,255,255,0.8);
            cursor: pointer; padding: 0; transition: transform 0.15s, box-shadow 0.15s; outline: none; flex-shrink: 0;
        }
        .clr-dot:hover { transform: scale(1.3); box-shadow: 0 0 8px #FFF; }

        /* ===== Floating Tactical Pin Control Bar ===== */
        #pinControlBar {
            position: absolute; bottom: 25px; left: 50%; transform: translateX(-50%);
            background: rgba(20, 10, 8, 0.96); border: 2px solid #FF4444; border-radius: 8px;
            padding: 8px 16px; display: none; align-items: center; gap: 10px;
            box-shadow: 0 4px 25px rgba(0,0,0,0.9), 0 0 15px rgba(255,68,68,0.3);
            z-index: 10000; font-family: 'Consolas', monospace; font-size: 11px; color: #FFE8E8;
        }
        .pcb-title { font-weight: bold; color: #FF4444; font-size: 12px; white-space: nowrap; margin-right: 4px; }

        /* ===== Tactical Radius Settings Box ===== */
        .tactical-cfg-box {
            position: absolute; top: 45px; left: 0;
            background: rgba(8, 14, 10, 0.97); border: 2px solid #00FF66; border-radius: 8px;
            padding: 12px 16px; box-shadow: 0 4px 25px rgba(0,0,0,0.95), 0 0 15px rgba(0,255,102,0.35);
            z-index: 10001; font-family: 'Consolas', monospace; font-size: 11px; color: #E0FFE8;
            width: 420px;
        }
        .tcb-header {
            display: flex; justify-content: space-between; align-items: center;
            border-bottom: 1px solid rgba(0,255,102,0.3); padding-bottom: 6px; margin-bottom: 10px;
        }
        .tcb-title {
            font-weight: bold; color: #00FF66; font-size: 12px; letter-spacing: 0.5px;
        }
        .tcb-close-btn {
            background: transparent; border: none; color: #888; font-size: 14px;
            cursor: pointer; padding: 0 4px; transition: color 0.2s;
        }
        .tcb-close-btn:hover { color: #FF4444; }

        /* Weapon selection cards */
        .wpn-btn {
            flex: 1; padding: 8px 10px; background: rgba(0, 30, 20, 0.8);
            border: 2px solid rgba(0, 170, 85, 0.5); border-radius: 6px;
            color: #E0FFE8; font-family: inherit; text-align: left;
            cursor: pointer; transition: all 0.2s;
        }
        .wpn-btn:hover {
            background: rgba(0, 80, 45, 0.85); border-color: #00FF66;
            box-shadow: 0 0 10px rgba(0,255,102,0.4);
        }
        .wpn-btn.active {
            background: rgba(0, 120, 60, 0.9); border-color: #00FF66;
            box-shadow: 0 0 14px rgba(0,255,102,0.6);
        }
        .wpn-btn.active .wpn-title { color: #00FF66; }

        /* Mode selection buttons */
        .mode-btn {
            flex: 1; padding: 4px 6px; background: rgba(0, 20, 30, 0.8);
            border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 4px;
            color: #BAE6FD; font-family: inherit; font-size: 10px;
            cursor: pointer; transition: all 0.2s; text-align: center;
        }
        .mode-btn:hover { background: rgba(0, 60, 90, 0.85); border-color: #38BDF8; }
        .mode-btn.active {
            background: #0284C7; color: #FFF; font-weight: bold;
            border-color: #38BDF8; box-shadow: 0 0 8px rgba(56,189,248,0.5);
        }

        /* 3-Zone preview card */
        .tcb-preview-card {
            background: rgba(4, 8, 6, 0.95); border: 1px solid rgba(0, 255, 102, 0.25);
            border-radius: 6px; padding: 8px 12px; margin-bottom: 10px;
        }
        .tcb-zone-row {
            display: flex; align-items: center; justify-content: space-between;
            padding: 3px 8px; margin: 3px 0; background: rgba(255,255,255,0.03);
            border-radius: 3px; font-size: 11px;
        }
        .badge-num {
            padding: 2px 6px; border-radius: 3px; font-weight: bold; font-family: inherit;
            min-width: 60px; text-align: right; font-size: 11px;
        }

        /* Tactical data table */
        .tcb-table {
            width: 100%; border-collapse: collapse; font-size: 10px; margin-top: 4px;
        }
        .tcb-table th {
            background: rgba(0, 40, 25, 0.8); color: #00FF66; padding: 4px 6px;
            text-align: left; border: 1px solid rgba(0, 170, 85, 0.3);
        }
        .tcb-table td {
            padding: 3px 6px; border: 1px solid rgba(0, 170, 85, 0.2);
            color: #C8E6C9; background: rgba(0, 10, 8, 0.6);
        }
        .tcb-table tr:nth-child(even) td { background: rgba(0, 20, 12, 0.6); }

        .tcb-inp {
            background: rgba(0,0,0,0.8); border: 1px solid #00AA55;
            color: #FFF; padding: 3px 8px; border-radius: 4px; font-family: inherit;
            font-size: 11px;
        }
        .tcb-inp:focus { border-color: #00FF66; outline: none; box-shadow: 0 0 6px rgba(0,255,102,0.4); }

        /* Cesium overrides */
        .cesium-viewer-bottom { display: none !important; }
    </style>
</head>
<body>
    <div id="cesiumContainer"></div>
    <div id="controlPanel">
        <button id="pinModeBtn" class="tactical-btn" onclick="togglePinMode()" style="background: rgba(0, 100, 50, 0.8); border-color: #00FF66; margin-right: 6px;">🎯 PIN MODE: OFF</button>
        <button id="radiusCfgBtn" class="tactical-btn" onclick="toggleRadiusConfig()" style="background: rgba(0, 70, 110, 0.8); border-color: #38BDF8; margin-right: 6px;">⚙️ MK-82 (🔴9m 🟠15.2m 🟡1219m)</button>
        <button class="tactical-btn" onclick="deleteLastPin()" style="background: rgba(139, 0, 0, 0.85); border-color: #FF4444; margin-right: 6px;">🗑️ DEL LAST PIN</button>
        <button class="tactical-btn" onclick="clearAllPins()" style="background: rgba(60, 20, 20, 0.8); border-color: #884444; font-size: 10px; opacity: 0.8;">❌ CLEAR ALL</button>

        <div id="radiusConfigBox" class="tactical-cfg-box" style="display: none;">
            <div class="tcb-header">
                <span class="tcb-title">❖ WEAPON EFFECT RADIUS PRESET</span>
                <button onclick="toggleRadiusConfig()" class="tcb-close-btn" title="Close">✖</button>
            </div>
            
            <!-- Weapon Preset Selector (MK-82 / MK-84) -->
            <div style="margin-bottom: 8px;">
                <div style="color: #38BDF8; font-weight: bold; margin-bottom: 5px; font-size: 11px;">🚀 SELECT WEAPON (เลือกหัวข้อรัศมีอาวุธ):</div>
                <div style="display: flex; gap: 8px;">
                    <button id="wpnBtnMK82" class="wpn-btn active" onclick="selectWeapon('MK-82')">
                        <div class="wpn-title" style="font-size: 12px; font-weight: bold;">💣 MK-82</div>
                        <div style="font-size: 9px; opacity: 0.85; color: #A8FFB8;">500 lb GP Bomb</div>
                    </button>
                    <button id="wpnBtnMK84" class="wpn-btn" onclick="selectWeapon('MK-84')">
                        <div class="wpn-title" style="font-size: 12px; font-weight: bold;">💣 MK-84</div>
                        <div style="font-size: 9px; opacity: 0.85; color: #A8FFB8;">2,000 lb GP Bomb</div>
                    </button>
                </div>
            </div>

            <!-- Effect Mode Selector -->
            <div style="margin-bottom: 8px;">
                <div style="color: #A8FFB8; font-weight: bold; margin-bottom: 4px; font-size: 10px;">🎯 EFFECT VIEW MODE (รูปแบบโซน 3 สี):</div>
                <div style="display: flex; gap: 4px;">
                    <button id="modeBtnFull" class="mode-btn active" onclick="selectEffectMode('full')">Full Effect (Pen/Blast/Frag)</button>
                    <button id="modeBtnFrag" class="mode-btn" onclick="selectEffectMode('frag')">Frag (Front/Rear/Side)</button>
                    <button id="modeBtnPen" class="mode-btn" onclick="selectEffectMode('penetration')">Crater & Upheaval</button>
                </div>
            </div>

            <!-- Active 3-Zone Display Preview -->
            <div class="tcb-preview-card">
                <div style="font-weight: bold; color: #FFF; margin-bottom: 5px; display: flex; justify-content: space-between; align-items: center;">
                    <span id="cfgActiveName" style="color: #00FF66;">💣 MK-82 ACTIVE PRESET</span>
                    <span id="cfgActiveModeLabel" style="color: #38BDF8; font-size: 10px; font-weight: normal;">Full Effect</span>
                </div>
                <div class="tcb-zone-row" style="border-left: 3px solid #FF4444;">
                    <span style="color: #FF6666; font-weight: bold;">🔴 Red (Inner):</span>
                    <span id="valRedDesc" style="color: #FFE0E0; font-size: 10px;">Penetration Crater</span>
                    <span id="valRedNum" class="badge-num" style="background: rgba(255,50,50,0.25); color: #FF7777;">9 m</span>
                </div>
                <div class="tcb-zone-row" style="border-left: 3px solid #FFA500;">
                    <span style="color: #FFA500; font-weight: bold;">🟠 Orange (Mid):</span>
                    <span id="valOrangeDesc" style="color: #FFE8CC; font-size: 10px;">Blast Wave (50')</span>
                    <span id="valOrangeNum" class="badge-num" style="background: rgba(255,165,0,0.25); color: #FFA500;">15.2 m</span>
                </div>
                <div class="tcb-zone-row" style="border-left: 3px solid #FFFF44;">
                    <span style="color: #FFFF44; font-weight: bold;">🟡 Yellow (Outer):</span>
                    <span id="valYellowDesc" style="color: #FFFFCC; font-size: 10px;">Frag Beside (4,000')</span>
                    <span id="valYellowNum" class="badge-num" style="background: rgba(255,255,50,0.25); color: #FFFF44;">1,219 m</span>
                </div>
            </div>

            <!-- Ballistic Data Reference Table (From Image) -->
            <div style="margin-top: 6px;">
                <div style="font-weight: bold; color: #E0FFE8; font-size: 10px; margin-bottom: 3px; display: flex; align-items: center; justify-content: space-between;">
                    <span>📊 REFERENCE DATA (ตารางผลของอาวุธ):</span>
                    <span id="tblWpnTitle" style="color: #38BDF8; font-size: 10px;">MK-82 Data</span>
                </div>
                <table class="tcb-table">
                    <thead>
                        <tr>
                            <th>Effect Type</th>
                            <th>Parameter</th>
                            <th>Table Value</th>
                            <th>Terrain Radius</th>
                        </tr>
                    </thead>
                    <tbody id="refTableBody">
                        <!-- Populated dynamically by JS -->
                    </tbody>
                </table>
            </div>

            <!-- Pin Custom Label & Quick Close -->
            <div style="margin-top: 8px; display: flex; align-items: center; justify-content: space-between; gap: 6px;">
                <span style="color: #38BDF8; font-size: 10px; white-space: nowrap;">🏷️ Pin Label:</span>
                <input type="text" id="cfgPinLabel" class="tcb-inp" value="MK-82" style="width: 90px; text-align: center; padding: 2px 6px;">
                <button class="tactical-btn" onclick="applyPresetAndClose()" style="flex: 1; padding: 4px 8px; background: #00AA55; color: #000; border-color: #00FF66; font-size: 10px; font-weight: bold;">✓ APPLY & CLOSE</button>
            </div>
        </div>
    </div>
    <div id="minimapContainer"></div>

    <!-- 🕹️ Top Toolbar -->
    <div id="editToolbar">
        <button id="editModeBtn" class="tb-btn" onclick="toggleEditMode()">🔧 EDIT: OFF</button>
        <div class="tb-sep"></div>
        <select id="shapeSelect" class="tb-sel">
            <option value="box">📦 Box</option>
            <option value="cylinder">🛢️ Cylinder</option>
            <option value="cone">📐 Cone</option>
            <option value="sphere">⚽ Sphere</option>
            <option value="polygon">🛑 Polygon</option>
        </select>
        <div class="tb-sep"></div>
        <input id="latInput" class="tb-inp" placeholder="LAT" onkeydown="if(event.key==='Enter') searchAndFly()">
        <input id="lonInput" class="tb-inp" placeholder="LON" onkeydown="if(event.key==='Enter') searchAndFly()">
        <button class="tb-btn" onclick="searchAndFly()">🎯 FLY</button>
        <div class="tb-sep"></div>
        <button class="tb-btn" onclick="document.getElementById('imageFileInput').click()">🖼️ IMPORT IMAGE</button>
        <input type="file" id="imageFileInput" accept="image/*" style="display:none" onchange="handleImageUpload(event)">
        <div class="tb-sep"></div>
        <label style="color:#A8FFB8; font-size:11px; font-weight:bold;">🎨 COLOR:</label>
        <input type="color" id="toolbarColorPicker" value="#00E5FF" style="width:24px; height:24px; border:1px solid #00AA55; border-radius:4px; padding:0; background:#020604; cursor:pointer;" title="Choose color for new shapes" onchange="setGlobalDrawColor(this.value)">
        <div class="tb-sep"></div>
        <button class="tb-btn" onclick="reportStatus('EXPORT_3D_TRIGGER', '1')" style="background: rgba(0, 100, 150, 0.85); border-color: #38BDF8;">📤 EXPORT 3D</button>
    </div>

    <!-- 📋 Object Data Panel (right sidebar) -->
    <div id="objectPanel">
        <div class="pnl-hdr">
            <span>📋 OBJECT DATA</span>
            <span class="pnl-cnt" id="objCnt">0</span>
        </div>
        <div id="objList"></div>
    </div>

    <!-- 📐 Drawing Guide -->
    <div id="drawGuide">🎯 Click on map to place object</div>

    <!-- 🖼️ Floating Image Draft Control Bar -->
    <div id="imageControlBar">
        <div class="icb-title"><span id="icbName">🖼️ DRAFT</span></div>
        
        <div class="icb-group">
            <label>👁️ Opacity:</label>
            <input type="range" id="icbOpacity" min="0.1" max="1.0" step="0.05" value="0.85" oninput="setImageOpacity(this.value)">
            <span id="icbOpacityVal">85%</span>
        </div>

        <div class="icb-group">
            <label>↔ Scale:</label>
            <button class="icb-btn" onclick="stepImageScale(0.9)">➖</button>
            <input type="range" id="icbScale" min="0.1" max="5.0" step="0.05" value="1.0" oninput="setImageScaleSlider(this.value)">
            <button class="icb-btn" onclick="stepImageScale(1.1)">➕</button>
            <span id="icbScaleVal">1.0x</span>
        </div>

        <div class="icb-group">
            <label>🔄 Rotate:</label>
            <button class="icb-btn" onclick="stepImageRotate(-5)">↶</button>
            <input type="range" id="icbRotate" min="0" max="360" step="1" value="0" oninput="setImageRotateSlider(this.value)">
            <button class="icb-btn" onclick="stepImageRotate(5)">↷</button>
            <span id="icbRotateVal">0°</span>
        </div>

        <div class="icb-group">
            <label>✥ Nudge:</label>
            <button class="icb-btn" onclick="nudgeImage(0, 10)">⬆</button>
            <button class="icb-btn" onclick="nudgeImage(0, -10)">⬇</button>
            <button class="icb-btn" onclick="nudgeImage(-10, 0)">⬅</button>
            <button class="icb-btn" onclick="nudgeImage(10, 0)">➡</button>
        </div>

        <button id="icbLockBtn" class="icb-btn lock" onclick="toggleImageLock()">🔓 UNLOCKED</button>
        <button class="icb-btn del" onclick="deleteActiveImage()">🗑️ DELETE</button>
        <button class="icb-btn close" onclick="closeImageControlBar()">✖</button>
    </div>

    <!-- 🏢 Floating 3D Object Control Bar (Resize & Height) -->
    <div id="objectControlBar">
        <div class="ocb-title"><span id="ocbName">🏢 OBJECT</span></div>
        
        <div class="ocb-group">
            <label>📏 Height:</label>
            <button class="icb-btn" onclick="modifyActiveObject(1.0, -5)" title="ลดความสูง 5m">➖5m</button>
            <div style="display:inline-flex; align-items:center; gap:2px;">
                <input type="number" id="ocbHeightInput" class="ocb-inp" min="1" max="10000" step="1" value="20"
                       title="กรอกตัวเลขความสูงโดยตรง (กด Enter เพื่อปรับ)"
                       onchange="setActiveObjectHeight(this.value)"
                       onkeydown="if(event.key==='Enter'){ setActiveObjectHeight(this.value); this.blur(); }">
                <span style="color:#00FF66; font-size:11px; font-weight:bold;">m</span>
            </div>
            <span id="ocbHeightVal" style="display:none;">20m</span>
            <button class="icb-btn" onclick="modifyActiveObject(1.0, 5)" title="เพิ่มความสูง 5m">➕5m</button>
            <button class="icb-btn" onclick="modifyActiveObject(1.0, 20)" title="เพิ่มความสูง 20m">➕20m</button>
        </div>

        <div class="ocb-group">
            <label>↔ Size / Scale:</label>
            <button class="icb-btn" onclick="modifyActiveObject(0.85, 0)">➖15%</button>
            <span id="ocbSizeVal" style="min-width:38px; text-align:center; font-weight:bold; color:#38BDF8;">50m</span>
            <button class="icb-btn" onclick="modifyActiveObject(1.15, 0)">➕15%</button>
        </div>

        <div class="ocb-group">
            <label>🎨 Color:</label>
            <button class="clr-dot" style="background:#00E5FF;" title="Cyan" onclick="setActiveObjectColor('#00E5FF')"></button>
            <button class="clr-dot" style="background:#FFA500;" title="Orange" onclick="setActiveObjectColor('#FFA500')"></button>
            <button class="clr-dot" style="background:#FF3333;" title="Red" onclick="setActiveObjectColor('#FF3333')"></button>
            <button class="clr-dot" style="background:#00FF66;" title="Green" onclick="setActiveObjectColor('#00FF66')"></button>
            <button class="clr-dot" style="background:#FFFF33;" title="Yellow" onclick="setActiveObjectColor('#FFFF33')"></button>
            <button class="clr-dot" style="background:#D946EF;" title="Magenta" onclick="setActiveObjectColor('#D946EF')"></button>
            <button class="clr-dot" style="background:#3B82F6;" title="Blue" onclick="setActiveObjectColor('#3B82F6')"></button>
            <button class="clr-dot" style="background:#FFFFFF;" title="White" onclick="setActiveObjectColor('#FFFFFF')"></button>
            <input type="color" id="ocbCustomColor" value="#00E5FF" style="width:22px; height:22px; border:none; padding:0; background:transparent; cursor:pointer;" onchange="setActiveObjectColor(this.value)" title="Custom Color">
        </div>

        <button class="icb-btn" onclick="flyToActiveObject()" style="background:#00AA55; color:#000;">🎯 FLY</button>
        <button class="icb-btn del" onclick="deleteActiveObject()">🗑️ DELETE</button>
        <button class="icb-btn close" onclick="closeObjectControlBar()">✖</button>
    </div>

    <!-- 🎯 Floating Tactical Pin Control Bar -->
    <div id="pinControlBar">
        <div class="pcb-title"><span id="pcbName">🎯 PIN</span></div>
        <span id="pcbInfo" style="color: #FDE047; font-size: 11px;"></span>
        <button class="icb-btn" onclick="flyToActivePin()" style="background:#00AA55; color:#000;">🎯 FLY</button>
        <button class="icb-btn del" onclick="deleteActivePin()">🗑️ DELETE THIS PIN</button>
        <button class="icb-btn close" onclick="closePinControlBar()">✖</button>
    </div>

    <script>
        // ===== Status Reporting (JS → Python via document.title) =====
        function reportStatus(type, msg) { document.title = type + '|' + msg; }
        reportStatus('LOG', 'Initializing Interactive Edit Mode Engine...');

        // ===== Shape Configuration =====
        const SCFG = {
            box:      { icon: '📦', label: 'BOX',      clr: [0,1,1],     out: [1,1,1]     },
            cylinder: { icon: '🛢️', label: 'CYLINDER', clr: [0,1,0],     out: [1,1,1]     },
            cone:     { icon: '📐', label: 'CONE',      clr: [1,1,0],     out: [1,0.2,0.2] },
            sphere:   { icon: '⚽', label: 'SPHERE',    clr: [1,0,1],     out: [1,1,1]     },
            polygon:  { icon: '🛑', label: 'POLYGON',   clr: [1,0.65,0],  out: [1,1,0]     }
        };
        function sColor(arr) { return new Cesium.Color(arr[0], arr[1], arr[2], 1.0); }
        function sColorA(arr, a) { return new Cesium.Color(arr[0], arr[1], arr[2], a); }

        function hexToRgb(hex) {
            var c = hex.replace('#', '');
            if (c.length === 3) c = c.split('').map(function(ch) { return ch + ch; }).join('');
            var num = parseInt(c, 16);
            return [
                ((num >> 16) & 255) / 255,
                ((num >> 8) & 255) / 255,
                (num & 255) / 255
            ];
        }

        function rgbToHex(r, g, b) {
            var toH = function(n) {
                var h = Math.round(Math.max(0, Math.min(255, n * 255))).toString(16);
                return h.length === 1 ? '0' + h : h;
            };
            return '#' + toH(r) + toH(g) + toH(b);
        }

        let currentDrawColor = '#00E5FF';

        window.setGlobalDrawColor = function(hexColor) {
            currentDrawColor = hexColor;
            if (selectedObjectId !== null) {
                modifyObjColor(selectedObjectId, hexColor);
            }
            reportStatus('LOG', 'Draw color set to ' + hexColor);
        };

        // ===== Global State =====
        let editMode = false;
        let isDrawing = false;
        let drawState = null;   // { lat, lon, terrainHeight, startCartesian }
        let drawSize = 50;
        let previewEntity = null;
        let objectRegistry = []; // array of object data
        let selectedObjectId = null;
        let nextObjId = 1;

        // ===== Cesium Initialization =====
        Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJkYTg5NWUyOS1mOWFkLTRjNzAtYmNjNS0wOTE4ZmFiZTQwMDkiLCJpZCI6NDMxODUwLCJpc3MiOiJodHRwczovL2lvbi5jZXNpdW0uY29tIiwiYXVkIjoidW5kZWZpbmVkX2RlZmF1bHQiLCJpYXQiOjE3Nzg4MjM5NzJ9.NGxpk2bbxrmO4Z5eLJ8YVMV-xVNsTVNO9QeSvAuGy18';

        let viewer;
        try {
            viewer = new Cesium.Viewer('cesiumContainer', {
                imageryProvider: false, baseLayerPicker: false, animation: false, timeline: false,
                infoBox: false, selectionIndicator: false, navigationHelpButton: false, geocoder: false,
                homeButton: false, sceneModePicker: false, skyBox: false, skyAtmosphere: false
            });

            viewer.scene.backgroundColor = Cesium.Color.BLACK;
            viewer.scene.globe.depthTestAgainstTerrain = true;
            viewer.scene.globe.enableLighting = true;

            // 🏔️ 3D World Terrain
            Cesium.createWorldTerrainAsync({ requestWaterMask: true, requestVertexNormals: true })
                .then(function(tp) { viewer.terrainProvider = tp; reportStatus('LOG', '3D Terrain loaded.'); })
                .catch(function() { viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider(); });

            // 🌍 Satellite Imagery
            Cesium.createWorldImageryAsync({ style: Cesium.IonWorldImageryStyle.AERIAL_WITH_LABELS })
                .then(function(ip) { viewer.imageryLayers.addImageryProvider(ip); })
                .catch(function() {
                    viewer.imageryLayers.addImageryProvider(new Cesium.UrlTemplateImageryProvider({
                        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
                    }));
                });

            // Camera limits
            var camCtrl = viewer.scene.screenSpaceCameraController;
            camCtrl.minimumZoomDistance = 50.0;
            camCtrl.maximumZoomDistance = 8000.0;

            // 🏢 OSM 3D Buildings (built-in — ไม่ยุ่ง)
            Cesium.createOsmBuildingsAsync().then(function(t) {
                viewer.scene.primitives.add(t);
                reportStatus('LOG', '3D Buildings loaded.');
            }).catch(function() {});

            // Initial camera — พิกัดเริ่มต้นที่ประเทศไทย (กรุงเทพฯ / Thailand)
            viewer.scene.camera.setView({
                destination: Cesium.Cartesian3.fromDegrees(100.5018, 13.7563, 3000),
                orientation: {
                    heading: Cesium.Math.toRadians(0),
                    pitch: Cesium.Math.toRadians(-35),
                    roll: 0.0
                }
            });

            // =================================================================
            // MINIMAP 2D & TACTICAL PINS
            // =================================================================
            const minimapViewer = new Cesium.Viewer('minimapContainer', {
                imageryProvider: false, baseLayerPicker: false, animation: false, timeline: false,
                infoBox: false, selectionIndicator: false, navigationHelpButton: false, geocoder: false,
                homeButton: false, sceneModePicker: false, skyBox: false, skyAtmosphere: false,
                sceneMode: Cesium.SceneMode.SCENE2D
            });
            minimapViewer.scene.backgroundColor = Cesium.Color.BLACK;
            minimapViewer.scene.screenSpaceCameraController.enableRotate = false;
            minimapViewer.scene.screenSpaceCameraController.enableTranslate = true;
            minimapViewer.scene.screenSpaceCameraController.enableZoom = true;
            minimapViewer.scene.screenSpaceCameraController.enableTilt = false;
            minimapViewer.scene.screenSpaceCameraController.enableLook = false;
            
            minimapViewer.camera.setView({
                destination: Cesium.Cartesian3.fromDegrees(100.0, 13.0, 20000000)
            });

            Cesium.createWorldImageryAsync({ style: Cesium.IonWorldImageryStyle.AERIAL_WITH_LABELS })
                .then(function(ip) { minimapViewer.imageryLayers.addImageryProvider(ip); })
                .catch(function() {
                    minimapViewer.imageryLayers.addImageryProvider(new Cesium.UrlTemplateImageryProvider({
                        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
                    }));
                });
            
            var minimapMarker = minimapViewer.entities.add({
                position: Cesium.Cartesian3.fromDegrees(100.5018, 13.7563, 0),
                point: { pixelSize: 10, color: Cesium.Color.RED, outlineColor: Cesium.Color.WHITE, outlineWidth: 2 }
            });

            viewer.camera.changed.addEventListener(function() {
                var canvas = viewer.scene.canvas;
                var centerCartesian = viewer.camera.pickEllipsoid(new Cesium.Cartesian2(canvas.clientWidth / 2, canvas.clientHeight / 2), viewer.scene.globe.ellipsoid);
                
                if (!centerCartesian) {
                    const pos = viewer.camera.positionCartographic;
                    centerCartesian = Cesium.Cartesian3.fromRadians(pos.longitude, pos.latitude, 0);
                }
                
                minimapMarker.position = centerCartesian;
                minimapMarker.position = centerCartesian;
            });

            var minimapHandler = new Cesium.ScreenSpaceEventHandler(minimapViewer.scene.canvas);
            minimapHandler.setInputAction(function(ev) {
                var cartesian = minimapViewer.camera.pickEllipsoid(ev.position, minimapViewer.scene.globe.ellipsoid);
                if (cartesian) {
                    var carto = Cesium.Cartographic.fromCartesian(cartesian);
                    viewer.camera.flyTo({
                        destination: Cesium.Cartesian3.fromRadians(carto.longitude, carto.latitude, viewer.camera.positionCartographic.height),
                        duration: 1.5
                    });
                }
            }, Cesium.ScreenSpaceEventType.LEFT_CLICK);




            // =================================================================
            // EDIT MODE SYSTEM — ระบบวาด/แก้ไข/ลบ วัตถุ 3D แบบ Interactive
            // =================================================================

            // 🔧 Toggle Edit Mode
            window.toggleEditMode = function(forceState) {
                editMode = (typeof forceState === 'boolean') ? forceState : !editMode;
                var btn = document.getElementById('editModeBtn');
                var guide = document.getElementById('drawGuide');

                if (editMode) {
                    if (pinMode) togglePinMode(false);
                    btn.textContent = '🔧 EDIT: ON';
                    btn.classList.add('active');
                    guide.style.display = 'block';
                    guide.textContent = '🎯 Select shape and click on map to start';
                } else {
                    btn.textContent = '🔧 EDIT: OFF';
                    btn.classList.remove('active');
                    guide.style.display = 'none';
                    if (isDrawing) cancelDrawing();
                    deselectAll();
                }
                reportStatus('EDIT_MODE', editMode ? 'ON' : 'OFF');
            };

            // 📍 Position picker helper (picks terrain through imagery overlays)
            function pickPos(screenPos) {
                var ray = viewer.camera.getPickRay(screenPos);
                var c = viewer.scene.globe.pick(ray, viewer.scene);
                if (!Cesium.defined(c)) c = viewer.scene.pickPosition(screenPos);
                if (!Cesium.defined(c)) c = viewer.camera.pickEllipsoid(screenPos, viewer.scene.globe.ellipsoid);
                return c || null;
            }

            // =================================================================
            // DRAWING ENGINE — Click-Drag-Release ระบบวาดวัตถุ 3D
            // =================================================================
            var handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);

            // =================================================================
            // PIN MODE & TACTICAL RADIUS SYSTEM — โหมดวางหมุดและตั้งค่ารัศมีอาวุธ
            // Preset อาวุธ MK-82 และ MK-84 ตามตาราง Weapon Effect
            // =================================================================
            let pinMode = false;
            let pinRegistry = [];

            function formatR(val) {
                if (val === undefined || val === null) return '';
                var num = Number(val);
                if (isNaN(num)) return val + '';
                return (Number.isInteger(num) ? num : num.toFixed(1)) + 'm';
            }

            const WEAPON_PRESETS = {
                'MK-82': {
                    name: 'MK-82',
                    desc: '500 lb GP Bomb',
                    modes: {
                        'full': {
                            title: 'Full Effect (Pen/Blast/Frag)',
                            rRed: 9,       // Crater 9m
                            rOrange: 15.2, // Blast 50' ≈ 15.24m
                            rYellow: 1219, // Frag Beside 4,000' ≈ 1,219.2m
                            descRed: 'Penetration Crater',
                            descOrange: "Blast Wave (50')",
                            descYellow: "Frag Beside (4,000')"
                        },
                        'frag': {
                            title: 'Fragmentation (Front/Rear/Side)',
                            rRed: 640,     // Front 2,100' ≈ 640m
                            rOrange: 914,  // Rear 3,000' ≈ 914m
                            rYellow: 1219, // Beside 4,000' ≈ 1,219m
                            descRed: "Frag Front (2,100')",
                            descOrange: "Frag Rear (3,000')",
                            descYellow: "Frag Beside (4,000')"
                        },
                        'penetration': {
                            title: 'Crater & Upheaval',
                            rRed: 9,       // Crater 9m
                            rOrange: 11,   // Upheaval 11m
                            rYellow: 15.2, // Blast 50' ≈ 15.2m
                            descRed: 'Crater (9m)',
                            descOrange: 'Upheaval (11m)',
                            descYellow: "Blast Wave (50')"
                        }
                    },
                    tableRows: [
                        { type: 'Blast', param: 'Area coverage', raw: "50'", meters: '15.2 m' },
                        { type: 'Fragment', param: 'Front', raw: "2,100'", meters: '640 m' },
                        { type: 'Fragment', param: 'Rear', raw: "3,000'", meters: '914 m' },
                        { type: 'Fragment', param: 'Beside', raw: "4,000'", meters: '1,219 m' },
                        { type: 'Penetration', param: 'Crater', raw: '9 m', meters: '9 m' },
                        { type: 'Penetration', param: 'Upheaval', raw: '11 m', meters: '11 m' }
                    ]
                },
                'MK-84': {
                    name: 'MK-84',
                    desc: '2,000 lb GP Bomb',
                    modes: {
                        'full': {
                            title: 'Full Effect (Pen/Blast/Frag)',
                            rRed: 15,      // Crater 15m
                            rOrange: 26.2, // Blast 86' ≈ 26.21m
                            rYellow: 4877, // Frag Beside 16,000' ≈ 4,876.8m
                            descRed: 'Penetration Crater',
                            descOrange: "Blast Wave (86')",
                            descYellow: "Frag Beside (16,000')"
                        },
                        'frag': {
                            title: 'Fragmentation (Front/Rear/Side)',
                            rRed: 3962,    // Front 13,000' ≈ 3,962.4m
                            rOrange: 3962, // Rear 13,000' ≈ 3,962.4m
                            rYellow: 4877, // Beside 16,000' ≈ 4,876.8m
                            descRed: "Frag Front (13,000')",
                            descOrange: "Frag Rear (13,000')",
                            descYellow: "Frag Beside (16,000')"
                        },
                        'penetration': {
                            title: 'Crater & Upheaval',
                            rRed: 15,      // Crater 15m
                            rOrange: 19.5, // Upheaval 19.5m
                            rYellow: 26.2, // Blast 86' ≈ 26.2m
                            descRed: 'Crater (15m)',
                            descOrange: 'Upheaval (19.5m)',
                            descYellow: "Blast Wave (86')"
                        }
                    },
                    tableRows: [
                        { type: 'Blast', param: 'Area coverage', raw: "86'", meters: '26.2 m' },
                        { type: 'Fragment', param: 'Front', raw: "13,000'", meters: '3,962 m' },
                        { type: 'Fragment', param: 'Rear', raw: "13,000'", meters: '3,962 m' },
                        { type: 'Fragment', param: 'Beside', raw: "16,000'", meters: '4,877 m' },
                        { type: 'Penetration', param: 'Crater', raw: '15 m', meters: '15 m' },
                        { type: 'Penetration', param: 'Upheaval', raw: '19.5 m', meters: '19.5 m' }
                    ]
                }
            };

            let currentWeaponKey = 'MK-82';
            let currentEffectMode = 'full';

            let tacticalRadiusConfig = {
                weapon: 'MK-82',
                mode: 'full',
                rRed: 9,
                rOrange: 15.2,
                rYellow: 1219,
                label: "MK-82"
            };

            window.togglePinMode = function(forceState) {
                pinMode = (typeof forceState === 'boolean') ? forceState : !pinMode;
                var btn = document.getElementById('pinModeBtn');
                if (pinMode) {
                    btn.textContent = '🎯 PIN MODE: ON';
                    btn.style.background = '#00FF66';
                    btn.style.color = '#000000';
                    btn.style.boxShadow = '0 0 15px rgba(0, 255, 102, 0.8)';
                    if (editMode) toggleEditMode(false);
                    reportStatus('LOG', 'Pin Mode: ON (คลิกบนแผนที่เพื่อวางจุดรัศมี ' + tacticalRadiusConfig.label + ' 🔴' + formatR(tacticalRadiusConfig.rRed) + ' 🟠' + formatR(tacticalRadiusConfig.rOrange) + ' 🟡' + formatR(tacticalRadiusConfig.rYellow) + ')');
                } else {
                    btn.textContent = '🎯 PIN MODE: OFF';
                    btn.style.background = 'rgba(0, 100, 50, 0.8)';
                    btn.style.color = '#FFFFFF';
                    btn.style.boxShadow = 'none';
                    reportStatus('LOG', 'Pin Mode: OFF');
                }
            };

            window.toggleRadiusConfig = function() {
                var box = document.getElementById('radiusConfigBox');
                if (box) {
                    var isHidden = (box.style.display === 'none' || !box.style.display);
                    box.style.display = isHidden ? 'block' : 'none';
                    if (isHidden) updateConfigUI();
                }
            };

            window.selectWeapon = function(weaponKey) {
                if (!WEAPON_PRESETS[weaponKey]) return;
                var prevWeapon = currentWeaponKey;
                currentWeaponKey = weaponKey;
                
                var lblInp = document.getElementById('cfgPinLabel');
                if (lblInp && (lblInp.value === prevWeapon || lblInp.value === 'TGT' || !lblInp.value.trim())) {
                    lblInp.value = weaponKey;
                }
                
                applyWeaponConfig();
            };

            window.selectEffectMode = function(modeKey) {
                currentEffectMode = modeKey;
                applyWeaponConfig();
            };

            function applyWeaponConfig() {
                var wpn = WEAPON_PRESETS[currentWeaponKey];
                var modeData = wpn.modes[currentEffectMode] || wpn.modes['full'];
                var lbl = (document.getElementById('cfgPinLabel') ? document.getElementById('cfgPinLabel').value.trim() : '') || currentWeaponKey;

                tacticalRadiusConfig.weapon = currentWeaponKey;
                tacticalRadiusConfig.mode = currentEffectMode;
                tacticalRadiusConfig.rRed = modeData.rRed;
                tacticalRadiusConfig.rOrange = modeData.rOrange;
                tacticalRadiusConfig.rYellow = modeData.rYellow;
                tacticalRadiusConfig.label = lbl;

                var btn = document.getElementById('radiusCfgBtn');
                if (btn) {
                    btn.textContent = '⚙️ ' + currentWeaponKey + ' (🔴' + formatR(modeData.rRed) + ' 🟠' + formatR(modeData.rOrange) + ' 🟡' + formatR(modeData.rYellow) + ')';
                }

                updateConfigUI();
                reportStatus('LOG', 'Radius Preset Selected: ' + currentWeaponKey + ' [' + modeData.title + '] (🔴' + formatR(modeData.rRed) + ', 🟠' + formatR(modeData.rOrange) + ', 🟡' + formatR(modeData.rYellow) + ')');
            }

            function updateConfigUI() {
                var wpn = WEAPON_PRESETS[currentWeaponKey];
                var modeData = wpn.modes[currentEffectMode] || wpn.modes['full'];

                // Update weapon buttons
                var btn82 = document.getElementById('wpnBtnMK82');
                var btn84 = document.getElementById('wpnBtnMK84');
                if (btn82) btn82.className = 'wpn-btn' + (currentWeaponKey === 'MK-82' ? ' active' : '');
                if (btn84) btn84.className = 'wpn-btn' + (currentWeaponKey === 'MK-84' ? ' active' : '');

                // Update mode buttons
                var mFull = document.getElementById('modeBtnFull');
                var mFrag = document.getElementById('modeBtnFrag');
                var mPen = document.getElementById('modeBtnPen');
                if (mFull) mFull.className = 'mode-btn' + (currentEffectMode === 'full' ? ' active' : '');
                if (mFrag) mFrag.className = 'mode-btn' + (currentEffectMode === 'frag' ? ' active' : '');
                if (mPen) mPen.className = 'mode-btn' + (currentEffectMode === 'penetration' ? ' active' : '');

                // Update preview card
                var nameEl = document.getElementById('cfgActiveName');
                var modeEl = document.getElementById('cfgActiveModeLabel');
                if (nameEl) nameEl.textContent = '💣 ' + currentWeaponKey + ' (' + wpn.desc + ')';
                if (modeEl) modeEl.textContent = modeData.title;

                var dRed = document.getElementById('valRedDesc');
                var nRed = document.getElementById('valRedNum');
                if (dRed) dRed.textContent = modeData.descRed;
                if (nRed) nRed.textContent = formatR(modeData.rRed);

                var dOra = document.getElementById('valOrangeDesc');
                var nOra = document.getElementById('valOrangeNum');
                if (dOra) dOra.textContent = modeData.descOrange;
                if (nOra) nOra.textContent = formatR(modeData.rOrange);

                var dYel = document.getElementById('valYellowDesc');
                var nYel = document.getElementById('valYellowNum');
                if (dYel) dYel.textContent = modeData.descYellow;
                if (nYel) nYel.textContent = formatR(modeData.rYellow);

                // Update reference table
                var tblTitle = document.getElementById('tblWpnTitle');
                if (tblTitle) tblTitle.textContent = currentWeaponKey + ' Ballistic Specs';

                var tbody = document.getElementById('refTableBody');
                if (tbody) {
                    var html = '';
                    for (var i = 0; i < wpn.tableRows.length; i++) {
                        var row = wpn.tableRows[i];
                        html += '<tr><td><b>' + row.type + '</b></td><td>' + row.param + '</td><td><span style="color:#FDE047;">' + row.raw + '</span></td><td><span style="color:#00FF66; font-weight:bold;">' + row.meters + '</span></td></tr>';
                    }
                    tbody.innerHTML = html;
                }
            }

            window.applyPresetAndClose = function() {
                applyWeaponConfig();
                toggleRadiusConfig();
            };

            // Initialize UI once DOM ready
            setTimeout(function() {
                applyWeaponConfig();
            }, 300);

            // ฟังก์ชันสร้าง Tactical Pin Badge Canvas ที่มีสีสันสดใสบอกระยะรัศมีชัดเจน (แดง/ส้ม/เหลือง)
            function createPinBadgeCanvas(name, rRed, rOrange, rYellow) {
                var dpr = 2; // เพิ่มความคมชัดระดับ Retina
                var canvas = document.createElement('canvas');
                var ctx = canvas.getContext('2d');

                var fSize = 12 * dpr;
                ctx.font = 'bold ' + fSize + 'px Consolas, "Courier New", monospace';

                var txtName = (name || 'PIN').trim();
                var txtRed = formatR(rRed);
                var txtOra = formatR(rOrange);
                var txtYel = formatR(rYellow);

                var wName = ctx.measureText(txtName).width;
                var wRed = ctx.measureText(txtRed).width;
                var wOra = ctx.measureText(txtOra).width;
                var wYel = ctx.measureText(txtYel).width;

                var pillPadX = 7 * dpr;
                var dotR = 4 * dpr;
                var dotGap = 5 * dpr;
                var pillH = 20 * dpr;

                var wPillRed = pillPadX * 2 + (dotR * 2) + dotGap + wRed;
                var wPillOra = pillPadX * 2 + (dotR * 2) + dotGap + wOra;
                var wPillYel = pillPadX * 2 + (dotR * 2) + dotGap + wYel;

                var padX = 10 * dpr;
                var gap = 6 * dpr;
                var totalW = padX + wName + gap + (1 * dpr) + gap + wPillRed + gap + wPillOra + gap + wPillYel + padX;
                var badgeH = 32 * dpr;
                var arrowH = 7 * dpr;
                var totalH = badgeH + arrowH + (3 * dpr);

                canvas.width = Math.ceil(totalW + 6 * dpr);
                canvas.height = Math.ceil(totalH);

                ctx.font = 'bold ' + fSize + 'px Consolas, "Courier New", monospace';
                ctx.textBaseline = 'middle';

                var cornerR = 6 * dpr;
                var bx = 2 * dpr;
                var by = 2 * dpr;
                var bw = totalW;
                var bh = badgeH;

                function roundRectHelper(c, x, y, w, h, r) {
                    c.moveTo(x + r, y);
                    c.lineTo(x + w - r, y);
                    c.arcTo(x + w, y, x + w, y + r, r);
                    c.lineTo(x + w, y + h - r);
                    c.arcTo(x + w, y + h, x + w - r, y + h, r);
                    c.lineTo(x + r, y + h);
                    c.arcTo(x, y + h, x, y + h - r, r);
                    c.lineTo(x, y + r);
                    c.arcTo(x, y, x + r, y, r);
                }

                // วาดตัวกล่อง Badge พร้อมหัวลูกศรชี้ลงหมุด
                ctx.save();
                ctx.beginPath();
                ctx.moveTo(bx + cornerR, by);
                ctx.lineTo(bx + bw - cornerR, by);
                ctx.arcTo(bx + bw, by, bx + bw, by + cornerR, cornerR);
                ctx.lineTo(bx + bw, by + bh - cornerR);
                ctx.arcTo(bx + bw, by + bh, bx + bw - cornerR, by + bh, cornerR);
                var cx = bx + bw / 2;
                var aw = 7 * dpr;
                ctx.lineTo(cx + aw, by + bh);
                ctx.lineTo(cx, by + bh + arrowH);
                ctx.lineTo(cx - aw, by + bh);
                ctx.lineTo(bx + cornerR, by + bh);
                ctx.arcTo(bx, by + bh, bx, by + bh - cornerR, cornerR);
                ctx.lineTo(bx, by + cornerR);
                ctx.arcTo(bx, by, bx + cornerR, by, cornerR);
                ctx.closePath();

                ctx.fillStyle = 'rgba(6, 12, 10, 0.94)';
                ctx.shadowColor = 'rgba(0, 0, 0, 0.7)';
                ctx.shadowBlur = 10 * dpr;
                ctx.shadowOffsetY = 2 * dpr;
                ctx.fill();

                ctx.shadowColor = 'transparent';
                ctx.lineWidth = 1.5 * dpr;
                ctx.strokeStyle = '#00FF66';
                ctx.stroke();
                ctx.restore();

                // วาดชื่ออาวุธ/หมุด
                var curX = bx + padX;
                var textY = by + (badgeH / 2);

                ctx.fillStyle = '#FFFFFF';
                ctx.fillText(txtName, curX, textY);
                curX += wName + gap;

                // เส้นแบ่งแนวตั้ง
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.25)';
                ctx.lineWidth = 1 * dpr;
                ctx.beginPath();
                ctx.moveTo(curX, by + (badgeH - 14 * dpr) / 2);
                ctx.lineTo(curX, by + (badgeH + 14 * dpr) / 2);
                ctx.stroke();
                curX += (1 * dpr) + gap;

                function drawPill(text, textW, pillW, dotColor, textColor, bgColor, borderColor) {
                    var pillY = by + (badgeH - pillH) / 2;
                    var pR = 4 * dpr;

                    ctx.beginPath();
                    roundRectHelper(ctx, curX, pillY, pillW, pillH, pR);
                    ctx.closePath();
                    ctx.fillStyle = bgColor;
                    ctx.fill();
                    ctx.strokeStyle = borderColor;
                    ctx.lineWidth = 1 * dpr;
                    ctx.stroke();

                    var dX = curX + pillPadX + dotR;
                    var dY = by + (badgeH / 2);
                    ctx.beginPath();
                    ctx.arc(dX, dY, dotR, 0, Math.PI * 2);
                    ctx.fillStyle = dotColor;
                    ctx.fill();
                    ctx.strokeStyle = 'rgba(255,255,255,0.85)';
                    ctx.lineWidth = 0.8 * dpr;
                    ctx.stroke();

                    ctx.fillStyle = textColor;
                    ctx.fillText(text, dX + dotR + dotGap, textY);

                    curX += pillW + gap;
                }

                // 1. Red Zone (🔴 วงใน)
                drawPill(txtRed, wRed, wPillRed, '#FF3344', '#FF8888', 'rgba(255, 40, 40, 0.25)', 'rgba(255, 70, 70, 0.7)');
                // 2. Orange Zone (🟠 วงกลาง)
                drawPill(txtOra, wOra, wPillOra, '#FF9900', '#FFAA33', 'rgba(255, 140, 0, 0.25)', 'rgba(255, 165, 0, 0.7)');
                // 3. Yellow Zone (🟡 วงนอก)
                drawPill(txtYel, wYel, wPillYel, '#FFEE00', '#FFFF66', 'rgba(255, 230, 0, 0.25)', 'rgba(255, 235, 50, 0.7)');

                return canvas;
            }

            window.addPin = function(lat, lon, wName, rRed, rOrange, rYellow, alt) {
                rRed = rRed || tacticalRadiusConfig.rRed;
                rOrange = rOrange || tacticalRadiusConfig.rOrange;
                rYellow = rYellow || tacticalRadiusConfig.rYellow;
                wName = wName || tacticalRadiusConfig.label;
                alt = (typeof alt === 'number') ? alt : 0;

                var groupId = "PIN_" + Date.now();
                var pos = Cesium.Cartesian3.fromDegrees(lon, lat, alt);
                var groundPos = Cesium.Cartesian3.fromDegrees(lon, lat, 0);
                var pinEntities = [];

                // ฟังก์ชันสร้างวงรัศมีคู่ (แผ่นวงกลมแนบผิวพื้น + โดม 3D ลอยขึ้นฟ้า)
                var createRadiusZone = function(r, color, name) {
                    // 1. แผ่นวงกลมแนบชิดผิวพื้น Terrain 100% ไม่จมดินแม้ระยะจะเล็กเป็นเลขตัวเดียว
                    var groundRing = viewer.entities.add({
                        position: groundPos,
                        ellipse: {
                            semiMajorAxis: r,
                            semiMinorAxis: r,
                            material: color.withAlpha(0.35),
                            classificationType: Cesium.ClassificationType.TERRAIN
                        }
                    });
                    groundRing._pinGroupId = groupId;
                    pinEntities.push(groundRing);

                    // 2. โดม 3 มิติตั้งอยู่บนระดับความสูงพื้นดินจริง (alt) พุ่งขึ้นฟ้า
                    var dome = viewer.entities.add({
                        name: name,
                        position: pos,
                        ellipsoid: {
                            radii: new Cesium.Cartesian3(r, r, r),
                            material: color.withAlpha(0.18),
                            outline: true,
                            outlineColor: color
                        }
                    });
                    dome._pinGroupId = groupId;
                    pinEntities.push(dome);
                };

                // เรียงสร้างจากรัศมีใหญ่ไปเล็ก: เหลือง -> ส้ม -> แดง
                createRadiusZone(rYellow, Cesium.Color.YELLOW, wName + ' (Yellow ' + formatR(rYellow) + ')');
                createRadiusZone(rOrange, Cesium.Color.ORANGE, wName + ' (Orange ' + formatR(rOrange) + ')');
                createRadiusZone(rRed, Cesium.Color.RED, wName + ' (Red ' + formatR(rRed) + ')');

                // สร้างรูปภาพ Tactical Badge ที่แสดงระยะพร้อมแถบสีสันคมชัดระดับพิกเซล
                var badgeCanvas = createPinBadgeCanvas(wName, rRed, rOrange, rYellow);
                var badgeDataUrl = badgeCanvas.toDataURL();

                // หมุดจุดกึ่งกลางและ Tactical Badge แสดงรัศมีสีสันชัดเจน (ตั้งอยู่บนพื้นผิวจริง)
                var marker = viewer.entities.add({
                    position: pos,
                    point: {
                        pixelSize: 10,
                        color: Cesium.Color.WHITE,
                        outlineColor: Cesium.Color.BLACK,
                        outlineWidth: 2,
                        disableDepthTestDistance: Number.POSITIVE_INFINITY
                    },
                    billboard: {
                        image: badgeDataUrl,
                        verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
                        pixelOffset: new Cesium.Cartesian2(0, -8),
                        scale: 0.5,
                        disableDepthTestDistance: Number.POSITIVE_INFINITY
                    }
                });
                marker._pinGroupId = groupId;
                pinEntities.push(marker);

                pinRegistry.push({
                    id: groupId,
                    lat: lat,
                    lon: lon,
                    alt: alt,
                    label: wName,
                    rRed: rRed,
                    rOrange: rOrange,
                    rYellow: rYellow,
                    entities: pinEntities
                });

                reportStatus("LOG", "Dropped Pin: " + lat.toFixed(4) + ", " + lon.toFixed(4) + " [🔴" + formatR(rRed) + " 🟠" + formatR(rOrange) + " 🟡" + formatR(rYellow) + "]");
                syncDataToQt();
            };

            let selectedPinId = null;

            window.selectPin = function(pinId) {
                var p = pinRegistry.find(function(item) { return item.id === pinId; });
                if (p) {
                    selectedPinId = pinId;
                    openPinControlBar(p);
                } else {
                    selectedPinId = null;
                    closePinControlBar();
                }
            };

            function openPinControlBar(pin) {
                closeImageControlBar();
                closeObjectControlBar();
                var bar = document.getElementById('pinControlBar');
                if (!bar) return;
                bar.style.display = 'flex';
                document.getElementById('pcbName').textContent = '🎯 ' + pin.label;
                var infoEl = document.getElementById('pcbInfo');
                if (infoEl) {
                    infoEl.innerHTML = '📍 ' + pin.lat.toFixed(4) + ', ' + pin.lon.toFixed(4) + ' &nbsp;|&nbsp; ' +
                        '<span style="color:#FF6B6B; background:rgba(255,40,40,0.25); border:1px solid rgba(255,70,70,0.7); padding:2px 7px; border-radius:4px; font-weight:bold; margin-right:4px;">● ' + formatR(pin.rRed) + '</span>' +
                        '<span style="color:#FFAA33; background:rgba(255,140,0,0.25); border:1px solid rgba(255,165,0,0.7); padding:2px 7px; border-radius:4px; font-weight:bold; margin-right:4px;">● ' + formatR(pin.rOrange) + '</span>' +
                        '<span style="color:#FFFF66; background:rgba(255,230,0,0.25); border:1px solid rgba(255,235,50,0.7); padding:2px 7px; border-radius:4px; font-weight:bold;">● ' + formatR(pin.rYellow) + '</span>';
                }
            }

            window.closePinControlBar = function() {
                var bar = document.getElementById('pinControlBar');
                if (bar) bar.style.display = 'none';
            };

            window.deleteActivePin = function() {
                if (selectedPinId !== null) {
                    deletePin(selectedPinId);
                }
            };

            window.flyToActivePin = function() {
                if (selectedPinId !== null) {
                    flyToPin(selectedPinId);
                }
            };

            window.deletePin = function(pinId) {
                var idx = pinRegistry.findIndex(function(p) { return p.id === pinId; });
                if (idx !== -1) {
                    var p = pinRegistry[idx];
                    for (var j = 0; j < p.entities.length; j++) {
                        viewer.entities.remove(p.entities[j]);
                    }
                    pinRegistry.splice(idx, 1);
                    if (selectedPinId === pinId) {
                        closePinControlBar();
                        selectedPinId = null;
                    }
                    reportStatus("LOG", "Deleted Pin: " + p.label + " at " + p.lat.toFixed(4) + ", " + p.lon.toFixed(4));
                    syncDataToQt();
                }
            };

            window.deleteLastPin = function() {
                if (pinRegistry.length > 0) {
                    var last = pinRegistry[pinRegistry.length - 1];
                    deletePin(last.id);
                } else {
                    reportStatus("LOG", "No pins left to delete.");
                }
            };

            window.flyToPin = function(pinId) {
                var p = pinRegistry.find(function(item) { return item.id === pinId; });
                if (p && p.entities.length > 0) {
                    selectPin(pinId);
                    viewer.flyTo(p.entities[p.entities.length - 1], { duration: 1.5 });
                }
            };

            window.clearAllPins = function() {
                reportStatus("LOG", "Executing Clear All Pins Command...");
                for (var i = 0; i < pinRegistry.length; i++) {
                    var p = pinRegistry[i];
                    for (var j = 0; j < p.entities.length; j++) {
                        viewer.entities.remove(p.entities[j]);
                    }
                }
                pinRegistry = [];
                closePinControlBar();
                selectedPinId = null;
                reportStatus("LOG", "All Pins and 3D Domes cleared successfully.");
                syncDataToQt();
            };

            // ▶ LEFT_CLICK — สำหรับวางหมุดเฉพาะเมื่อเปิด Pin Mode
            handler.setInputAction(function(ev) {
                if (pinMode && !editMode) {
                    var cartesianPin = pickPos(ev.position);
                    if (cartesianPin) {
                        var carto = Cesium.Cartographic.fromCartesian(cartesianPin);
                        var pinLabel = (document.getElementById('cfgPinLabel') ? document.getElementById('cfgPinLabel').value.trim() : '') || tacticalRadiusConfig.label;
                        addPin(
                            Cesium.Math.toDegrees(carto.latitude),
                            Cesium.Math.toDegrees(carto.longitude),
                            pinLabel,
                            tacticalRadiusConfig.rRed,
                            tacticalRadiusConfig.rOrange,
                            tacticalRadiusConfig.rYellow,
                            carto.height || 0
                        );
                    }
                }
            }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

            var polygonMarkers = [];

            function clearPolygonMarkers() {
                for (var i = 0; i < polygonMarkers.length; i++) {
                    viewer.entities.remove(polygonMarkers[i]);
                }
                polygonMarkers = [];
            }

            function addPolygonVertexMarker(pos, isStart) {
                var ent = viewer.entities.add({
                    position: pos,
                    point: {
                        pixelSize: isStart ? 14 : 9,
                        color: isStart ? Cesium.Color.LIME : Cesium.Color.YELLOW,
                        outlineColor: Cesium.Color.WHITE,
                        outlineWidth: isStart ? 3 : 2,
                        disableDepthTestDistance: Number.POSITIVE_INFINITY
                    },
                    label: isStart ? {
                        text: "🟢 START / CLICK TO CLOSE",
                        font: "12px Consolas, monospace",
                        fillColor: Cesium.Color.WHITE,
                        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                        outlineColor: Cesium.Color.BLACK,
                        outlineWidth: 3,
                        pixelOffset: new Cesium.Cartesian2(0, -25),
                        disableDepthTestDistance: Number.POSITIVE_INFINITY
                    } : undefined
                });
                polygonMarkers.push(ent);
                return ent;
            }

            function finishPolygon() {
                if (!isDrawing || !drawState || drawState.points.length < 4) return;
                isDrawing = false;
                viewer.scene.screenSpaceCameraController.enableInputs = true;
                if (previewEntity) { viewer.entities.remove(previewEntity); previewEntity = null; }
                clearPolygonMarkers();
                
                // Remove the floating cursor point
                drawState.points.pop();
                
                buildObject('polygon', drawState.lat, drawState.lon, drawState.th, 0, drawState.points);
                drawState = null;
                document.getElementById('drawGuide').textContent = '🎯 Select shape and click on map to start';
            }

            // ▶ LEFT_DOWN — เริ่มวาด หรือ เลือกวัตถุ / Gizmo รูปภาพ
            handler.setInputAction(function(ev) {
                // 1. ถ้าคลิกโดน Gizmo Handle ของภาพ (เฉพาะเมื่อภาพไม่ได้ล็อก และยังไม่ได้เริ่มวาด Polygon)
                var picked = viewer.scene.pick(ev.position);
                if (Cesium.defined(picked) && Cesium.defined(picked.id) && picked.id._imgGizmo) {
                    var gz = picked.id._imgGizmo;
                    var img = gz.img;
                    if (!img.locked && !isDrawing) {
                        var cartesian = pickPos(ev.position);
                        if (cartesian) {
                            var carto = Cesium.Cartographic.fromCartesian(cartesian);
                            var clickLat = Cesium.Math.toDegrees(carto.latitude);
                            var clickLon = Cesium.Math.toDegrees(carto.longitude);

                            var dLatM = (clickLat - img.lat) * 111320;
                            var dLonM = (clickLon - img.lon) * 111320 * Math.cos(img.lat * Math.PI / 180);
                            var initialDist = Math.sqrt(dLatM * dLatM + dLonM * dLonM);
                            var initialBearing = Math.atan2(dLonM, dLatM) * 180 / Math.PI;

                            activeImageDrag = {
                                type: gz.type,
                                img: img,
                                startScale: img.scale,
                                startDist: Math.max(initialDist, 5),
                                startBearing: initialBearing,
                                startRot: img.rotation || 0,
                                startLat: img.lat,
                                startLon: img.lon,
                                startClickLat: clickLat,
                                startClickLon: clickLon
                            };
                            viewer.scene.screenSpaceCameraController.enableInputs = false;
                            return;
                        }
                    }
                }

                // 2. ถ้าคลิกโดนรูปภาพโดยตรง:
                // - ถ้า Edit Mode ปิดอยู่ -> เลือกภาพและเปิดแผงควบคุม
                // - ถ้า Edit Mode เปิดอยู่ -> ไม่ดักจับคลิก! ปล่อยให้ผ่านไปสร้างจุด Polygon ดราฟท์ทับบนภาพได้ 100%!
                if (!editMode && Cesium.defined(picked) && Cesium.defined(picked.id) && picked.id._imgId) {
                    selectImage(picked.id._imgId);
                    return;
                }

                // 3. ถ้าคลิกโดนหมุด Pin หรือโดมรัศมี (เมื่อไม่ได้อยู่ใน Edit Mode หรือ Pin Mode)
                if (!editMode && !pinMode && Cesium.defined(picked) && Cesium.defined(picked.id) && picked.id._pinGroupId) {
                    selectPin(picked.id._pinGroupId);
                    return;
                }

                if (!editMode) return;

                // ตรวจว่าคลิกโดนวัตถุ 3D อื่นๆ ที่สร้างไว้หรือไม่ (เฉพาะที่ไม่ใช่รูปภาพ)
                if (Cesium.defined(picked) && Cesium.defined(picked.id) && !picked.id._imgId) {
                    var ent = picked.id;
                    var found = objectRegistry.find(function(o) { return o.entity === ent || o.lblEnt === ent; });
                    if (found) {
                        selectObj(found.id);
                        return;
                    }
                }

                // เริ่มวาดวัตถุใหม่
                var cartesian = pickPos(ev.position);
                if (!cartesian) return;

                var shape = document.getElementById('shapeSelect').value;

                if (shape === 'polygon') {
                    if (!isDrawing) {
                        var carto = Cesium.Cartographic.fromCartesian(cartesian);
                        drawState = { 
                            lat: Cesium.Math.toDegrees(carto.latitude), 
                            lon: Cesium.Math.toDegrees(carto.longitude), 
                            th: carto.height || 0, 
                            points: [cartesian, cartesian] 
                        };
                        isDrawing = true;
                        viewer.scene.screenSpaceCameraController.enableInputs = false;
                        clearPolygonMarkers();
                        addPolygonVertexMarker(cartesian, true);
                        makePreview(shape);
                        document.getElementById('drawGuide').textContent = '📐 Click points to draw • Hover/Click start point or Double-Click to close';
                    } else {
                        // เช็คว่าคลิกบรรจบจุดเริ่มต้นหรือไม่ (จุดชน AutoCAD style)
                        var firstPtCanvas = Cesium.SceneTransforms.wgs84ToWindowCoordinates(viewer.scene, drawState.points[0]);
                        var distPixel = firstPtCanvas ? Cesium.Cartesian2.distance(firstPtCanvas, ev.position) : 999;
                        
                        if (drawState.points.length >= 4 && distPixel < 35) {
                            finishPolygon();
                        } else {
                            // เพิ่มจุดถัดไป
                            drawState.points[drawState.points.length - 1] = cartesian;
                            addPolygonVertexMarker(cartesian, false);
                            drawState.points.push(cartesian);
                        }
                    }
                    return;
                } else {
                    var carto = Cesium.Cartographic.fromCartesian(cartesian);
                    drawState = { lat: Cesium.Math.toDegrees(carto.latitude), lon: Cesium.Math.toDegrees(carto.longitude), th: carto.height || 0, startC: cartesian };
                    drawSize = 80;
                    isDrawing = true;
                    viewer.scene.screenSpaceCameraController.enableInputs = false;
                    makePreview(shape);
                    document.getElementById('drawGuide').textContent = '📐 Drag to resize • Release to place';
                }
            }, Cesium.ScreenSpaceEventType.LEFT_DOWN);

            // ▶ MOUSE_MOVE — อัปเดตขนาด Preview / Snapping / ลากปรับรูปภาพ
            handler.setInputAction(function(ev) {
                // ลากขยาย / หมุน / เคลื่อนย้ายรูปภาพด้วยเมาส์
                if (activeImageDrag) {
                    var cartesian = pickPos(ev.endPosition);
                    if (cartesian) {
                        var carto = Cesium.Cartographic.fromCartesian(cartesian);
                        var curLat = Cesium.Math.toDegrees(carto.latitude);
                        var curLon = Cesium.Math.toDegrees(carto.longitude);
                        var img = activeImageDrag.img;

                        if (activeImageDrag.type === 'scale') {
                            var dLatM = (curLat - img.lat) * 111320;
                            var dLonM = (curLon - img.lon) * 111320 * Math.cos(img.lat * Math.PI / 180);
                            var curDist = Math.sqrt(dLatM * dLatM + dLonM * dLonM);
                            var newScale = activeImageDrag.startScale * (curDist / activeImageDrag.startDist);
                            img.scale = Math.max(0.05, Math.min(50.0, newScale));
                            document.getElementById('drawGuide').textContent = '↔ ขยายภาพ: ' + img.scale.toFixed(2) + 'x (' + Math.round(img.baseWidth * img.scale) + 'm x ' + Math.round(img.baseHeight * img.scale) + 'm)';
                        } else if (activeImageDrag.type === 'rotate') {
                            var dLatM = (curLat - img.lat) * 111320;
                            var dLonM = (curLon - img.lon) * 111320 * Math.cos(img.lat * Math.PI / 180);
                            var curBearing = Math.atan2(dLonM, dLatM) * 180 / Math.PI;
                            var delta = curBearing - activeImageDrag.startBearing;
                            var newRot = (activeImageDrag.startRot + delta) % 360;
                            if (newRot < 0) newRot += 360;
                            img.rotation = Math.round(newRot);
                            document.getElementById('drawGuide').textContent = '🔄 หมุนภาพ: ' + img.rotation + '°';
                        } else if (activeImageDrag.type === 'move') {
                            var dLat = curLat - activeImageDrag.startClickLat;
                            var dLon = curLon - activeImageDrag.startClickLon;
                            img.lat = activeImageDrag.startLat + dLat;
                            img.lon = activeImageDrag.startLon + dLon;
                            document.getElementById('drawGuide').textContent = '✥ ย้ายภาพไปที่: ' + img.lat.toFixed(4) + ', ' + img.lon.toFixed(4);
                        }
                    }
                    return;
                }

                if (!isDrawing || !drawState) return;

                var cartesian = pickPos(ev.endPosition);
                if (!cartesian) return;
                
                var shape = document.getElementById('shapeSelect').value;

                if (shape === 'polygon') {
                    // AutoCAD Snapping: ถ้าลากเมาส์ใกล้จุดเริ่มต้น ให้ Snap เส้นเข้าหาจุดเริ่มทันที
                    if (drawState.points.length >= 4) {
                        var firstPtCanvas = Cesium.SceneTransforms.wgs84ToWindowCoordinates(viewer.scene, drawState.points[0]);
                        var distPixel = firstPtCanvas ? Cesium.Cartesian2.distance(firstPtCanvas, ev.endPosition) : 999;
                        if (distPixel < 35) {
                            drawState.points[drawState.points.length - 1] = drawState.points[0];
                            document.getElementById('drawGuide').textContent = '✨ CLICK TO CLOSE POLYGON & CREATE 3D BUILDING!';
                            return;
                        } else {
                            document.getElementById('drawGuide').textContent = '📐 Click points to draw • Hover/Click start point or Double-Click to close';
                        }
                    }
                    drawState.points[drawState.points.length - 1] = cartesian;
                } else {
                    var dist = Cesium.Cartesian3.distance(drawState.startC, cartesian);
                    drawSize = Math.max(dist, 5);
                    document.getElementById('drawGuide').textContent = '📐 Size: ' + Math.round(drawSize) + 'm • Release to confirm • ESC cancel';
                }
            }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);

            // ▶ LEFT_UP — ยืนยันสร้างวัตถุ / จบการลากรูปภาพ
            handler.setInputAction(function(ev) {
                if (activeImageDrag) {
                    activeImageDrag = null;
                    viewer.scene.screenSpaceCameraController.enableInputs = true;
                    document.getElementById('drawGuide').textContent = '🎯 Select shape and click on map to start';
                    syncDataToQt();
                    return;
                }

                if (!isDrawing || !drawState) return;
                var shape = document.getElementById('shapeSelect').value;
                if (shape === 'polygon') return; // Polygon จบด้วยการคลิกชนจุดเริ่ม หรือ Double-Click

                isDrawing = false;
                viewer.scene.screenSpaceCameraController.enableInputs = true;

                // ลบ Preview
                if (previewEntity) { viewer.entities.remove(previewEntity); previewEntity = null; }

                // สร้างวัตถุจริง
                var sz = Math.max(drawSize, 5);
                buildObject(shape, drawState.lat, drawState.lon, drawState.th, sz);

                drawState = null;
                document.getElementById('drawGuide').textContent = '🎯 Select shape and click on map to start';

            }, Cesium.ScreenSpaceEventType.LEFT_UP);

            // ▶ LEFT_DOUBLE_CLICK — จบการสร้าง Polygon ทันที
            handler.setInputAction(function(ev) {
                if (isDrawing && drawState) {
                    var shape = document.getElementById('shapeSelect').value;
                    if (shape === 'polygon' && drawState.points.length >= 4) {
                        finishPolygon();
                    }
                }
            }, Cesium.ScreenSpaceEventType.LEFT_DOUBLE_CLICK);

            // ▶ RIGHT_CLICK - ยกเลิกจุดล่าสุดของการวาด Polygon (Undo)
            handler.setInputAction(function(ev) {
                if (!isDrawing || !drawState) return;
                var shape = document.getElementById('shapeSelect').value;
                if (shape === 'polygon') {
                    if (drawState.points.length > 2) {
                        drawState.points.splice(drawState.points.length - 2, 1);
                        if (polygonMarkers.length > 1) {
                            var lastMarker = polygonMarkers.pop();
                            viewer.entities.remove(lastMarker);
                        }
                    } else {
                        cancelDrawing();
                    }
                }
            }, Cesium.ScreenSpaceEventType.RIGHT_CLICK);

            // ESC ยกเลิกการวาด
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape' && isDrawing) cancelDrawing();
            });

            function cancelDrawing() {
                isDrawing = false;
                drawState = null;
                viewer.scene.screenSpaceCameraController.enableInputs = true;
                if (previewEntity) { viewer.entities.remove(previewEntity); previewEntity = null; }
                clearPolygonMarkers();
                document.getElementById('drawGuide').textContent = '🎯 Click on map to place object • Drag to set size';
            }

            // =================================================================
            // PREVIEW ENTITY — วัตถุ Preview โปร่งแสงขณะวาด (CallbackProperty)
            // =================================================================
            function makePreview(shape) {
                var lon = drawState.lon, lat = drawState.lat, th = drawState.th;
                var rgb = hexToRgb(currentDrawColor || '#00E5FF');
                var matPrev = new Cesium.Color(rgb[0], rgb[1], rgb[2], 0.45);

                if (shape === 'box') {
                    previewEntity = viewer.entities.add({
                        position: new Cesium.CallbackProperty(function() {
                            return Cesium.Cartesian3.fromDegrees(lon, lat, th + (drawSize * 1.5) / 2);
                        }, false),
                        box: {
                            dimensions: new Cesium.CallbackProperty(function() {
                                return new Cesium.Cartesian3(drawSize, drawSize, drawSize * 1.5);
                            }, false),
                            material: matPrev, outline: false
                        }
                    });
                } else if (shape === 'cylinder') {
                    previewEntity = viewer.entities.add({
                        position: new Cesium.CallbackProperty(function() {
                            return Cesium.Cartesian3.fromDegrees(lon, lat, th + (drawSize * 1.5) / 2);
                        }, false),
                        cylinder: {
                            length: new Cesium.CallbackProperty(function() { return drawSize * 1.5; }, false),
                            topRadius: new Cesium.CallbackProperty(function() { return drawSize / 2; }, false),
                            bottomRadius: new Cesium.CallbackProperty(function() { return drawSize / 2; }, false),
                            material: matPrev, outline: false
                        }
                    });
                } else if (shape === 'cone') {
                    previewEntity = viewer.entities.add({
                        position: new Cesium.CallbackProperty(function() {
                            return Cesium.Cartesian3.fromDegrees(lon, lat, th + drawSize);
                        }, false),
                        cylinder: {
                            length: new Cesium.CallbackProperty(function() { return drawSize * 2; }, false),
                            topRadius: 0,
                            bottomRadius: new Cesium.CallbackProperty(function() { return drawSize / 2; }, false),
                            material: matPrev, outline: false
                        }
                    });
                } else if (shape === 'sphere') {
                    previewEntity = viewer.entities.add({
                        position: new Cesium.CallbackProperty(function() {
                            return Cesium.Cartesian3.fromDegrees(lon, lat, th + drawSize / 2);
                        }, false),
                        ellipsoid: {
                            radii: new Cesium.CallbackProperty(function() {
                                var r = drawSize / 2;
                                return new Cesium.Cartesian3(r, r, r);
                            }, false),
                            material: matPrev, outline: false
                        }
                    });
                } else if (shape === 'polygon') {
                    previewEntity = viewer.entities.add({
                        polyline: {
                            positions: new Cesium.CallbackProperty(function() {
                                return drawState ? drawState.points : [];
                            }, false),
                            width: 4,
                            material: new Cesium.ColorMaterialProperty(Cesium.Color.LIME),
                            depthFailMaterial: new Cesium.ColorMaterialProperty(Cesium.Color.LIME.withAlpha(0.6))
                        }
                    });
                }
            }

            // =================================================================
            // BUILD OBJECT — สร้างวัตถุ 3D จริง (Static Properties)
            // =================================================================
            function buildObject(shape, lat, lon, terrH, size, customPoints) {
                var id = nextObjId++;
                var cfg = SCFG[shape];
                var name = shape.toUpperCase() + '_' + id;
                var rgb = currentDrawColor ? hexToRgb(currentDrawColor) : cfg.clr;
                var mat = new Cesium.Color(rgb[0], rgb[1], rgb[2], 1.0);
                var out = new Cesium.Color(Math.min(1.0, rgb[0] * 1.2), Math.min(1.0, rgb[1] * 1.2), Math.min(1.0, rgb[2] * 1.2), 1.0);
                var entity = null;
                var obj = {
                    id: id, name: name, type: shape, lat: lat, lon: lon, th: terrH,
                    matArr: rgb, outArr: [out.red, out.green, out.blue],
                    colorHex: currentDrawColor || rgbToHex(rgb[0], rgb[1], rgb[2])
                };

                if (shape === 'box') {
                    var w = Math.round(size), d = Math.round(size), h = Math.round(size * 1.5);
                    entity = viewer.entities.add({
                        position: Cesium.Cartesian3.fromDegrees(lon, lat, terrH + h / 2),
                        box: { dimensions: new Cesium.Cartesian3(w, d, h), material: mat, outline: false }
                    });
                    obj.width = w; obj.depth = d; obj.height = h;

                } else if (shape === 'cylinder') {
                    var r = Math.round(size / 2), h = Math.round(size * 1.5);
                    entity = viewer.entities.add({
                        position: Cesium.Cartesian3.fromDegrees(lon, lat, terrH + h / 2),
                        cylinder: { length: h, topRadius: r, bottomRadius: r, material: mat, outline: false }
                    });
                    obj.radius = r; obj.height = h;

                } else if (shape === 'cone') {
                    var r = Math.round(size / 2), h = Math.round(size * 2);
                    entity = viewer.entities.add({
                        position: Cesium.Cartesian3.fromDegrees(lon, lat, terrH + h / 2),
                        cylinder: { length: h, topRadius: 0, bottomRadius: r, material: mat, outline: false }
                    });
                    obj.radius = r; obj.height = h;

                } else if (shape === 'sphere') {
                    var r = Math.round(size / 2);
                    entity = viewer.entities.add({
                        position: Cesium.Cartesian3.fromDegrees(lon, lat, terrH + r),
                        ellipsoid: { radii: new Cesium.Cartesian3(r, r, r), material: mat, outline: false }
                    });
                    obj.radius = r;

                } else if (shape === 'polygon') {
                    var polyPts;
                    var h = 20;
                    if (customPoints && customPoints.length >= 3) {
                        polyPts = customPoints;
                        var sX = 0, sY = 0, sZ = 0;
                        var minH = 99999;
                        for (var i = 0; i < polyPts.length; i++) {
                            sX += polyPts[i].x; sY += polyPts[i].y; sZ += polyPts[i].z;
                            var ptCarto = Cesium.Cartographic.fromCartesian(polyPts[i]);
                            if (ptCarto.height < minH) minH = ptCarto.height;
                        }
                        var c = new Cesium.Cartesian3(sX / polyPts.length, sY / polyPts.length, sZ / polyPts.length);
                        var carto = Cesium.Cartographic.fromCartesian(c);
                        lat = Cesium.Math.toDegrees(carto.latitude);
                        lon = Cesium.Math.toDegrees(carto.longitude);
                        obj.lat = lat; obj.lon = lon;

                        // ยึดฐานตึกให้ติดกับระดับ Terrain ของพื้นที่
                        if (minH < 90000 && minH > -500) {
                            terrH = minH;
                        } else if (carto.height) {
                            terrH = carto.height;
                        }
                    } else {
                        var dpm = 0.000009; var dd = size * dpm; h = Math.round(size * 1.5);
                        polyPts = Cesium.Cartesian3.fromDegreesArray([
                            lon-dd, lat-dd, lon+dd, lat-dd, lon+dd*1.3, lat,
                            lon+dd, lat+dd, lon-dd, lat+dd, lon-dd*1.3, lat
                        ]);
                    }
                    entity = viewer.entities.add({
                        polygon: {
                            hierarchy: new Cesium.PolygonHierarchy(polyPts),
                            height: terrH,
                            extrudedHeight: terrH + h,
                            material: mat,
                            outline: true,
                            outlineColor: out,
                            closeTop: true,
                            closeBottom: true
                        }
                    });
                    obj.size = Math.round(size); obj.height = h; obj.customPoints = customPoints;
                }

                // Label
                var lblEnt = viewer.entities.add({
                    position: Cesium.Cartesian3.fromDegrees(lon, lat, 0),
                    label: {
                        text: cfg.icon + ' ' + name,
                        font: '13px Consolas', fillColor: Cesium.Color.WHITE,
                        pixelOffset: new Cesium.Cartesian2(0, -30),
                        heightReference: Cesium.HeightReference.CLAMP_TO_TERRAIN,
                        disableDepthTestDistance: Number.POSITIVE_INFINITY
                    }
                });

                obj.entity = entity;
                obj.lblEnt = lblEnt;
                obj.matArr = cfg.clr;
                obj.outArr = cfg.out;
                objectRegistry.push(obj);

                refreshPanel();
                selectObj(id);
                reportStatus('LOG', 'Created ' + name + ' (' + Math.round(size) + 'm) at ' + lat.toFixed(4) + ', ' + lon.toFixed(4));
            }

            // =================================================================
            // SELECTION SYSTEM — เลือก/ยกเลิก/Highlight วัตถุ
            // =================================================================
            function selectObj(id) {
                deselectAll();
                var obj = objectRegistry.find(function(o) { return o.id === id; });
                if (!obj) return;

                selectedObjectId = id;
                hlEntity(obj, true);

                if (obj.entity) {
                    viewer.flyTo(obj.entity, {
                        offset: new Cesium.HeadingPitchRange(0, Cesium.Math.toRadians(-45), 1200),
                        duration: 1.0
                    });
                }
                openObjectControlBar(obj);
                refreshPanel();
            }
            window.selectObj = selectObj;

            function deselectAll() {
                if (selectedObjectId !== null) {
                    var prev = objectRegistry.find(function(o) { return o.id === selectedObjectId; });
                    if (prev) hlEntity(prev, false);
                }
                selectedObjectId = null;
                closeObjectControlBar();
            }

            function openObjectControlBar(obj) {
                closeImageControlBar();
                var bar = document.getElementById('objectControlBar');
                if (!bar) return;
                bar.style.display = 'flex';
                document.getElementById('ocbName').textContent = (SCFG[obj.type] ? SCFG[obj.type].icon : '🏢') + ' ' + obj.name;
                var h = Math.round(obj.height || 20);
                var sz = Math.round(obj.width || obj.radius || obj.size || 50);
                var inp = document.getElementById('ocbHeightInput');
                if (inp && document.activeElement !== inp) inp.value = h;
                var span = document.getElementById('ocbHeightVal');
                if (span) span.textContent = h + 'm';
                document.getElementById('ocbSizeVal').textContent = sz + 'm';
                var hex = obj.colorHex || rgbToHex(obj.matArr[0], obj.matArr[1], obj.matArr[2]);
                var inp = document.getElementById('ocbCustomColor');
                if (inp) inp.value = hex;
                var tbColor = document.getElementById('toolbarColorPicker');
                if (tbColor) tbColor.value = hex;
            }

            window.closeObjectControlBar = function() {
                var bar = document.getElementById('objectControlBar');
                if (bar) bar.style.display = 'none';
            };

            window.modifyActiveObject = function(deltaSizeFactor, deltaHeight) {
                if (selectedObjectId !== null) {
                    modifyObjDimensions(selectedObjectId, deltaSizeFactor, deltaHeight);
                }
            };

            window.flyToActiveObject = function() {
                if (selectedObjectId !== null) {
                    var obj = objectRegistry.find(function(o) { return o.id === selectedObjectId; });
                    if (obj && obj.entity) {
                        viewer.flyTo(obj.entity, { duration: 1.0 });
                    }
                }
            };

            window.deleteActiveObject = function() {
                if (selectedObjectId !== null) {
                    delObj(selectedObjectId);
                    closeObjectControlBar();
                }
            };

            window.setActiveObjectColor = function(hexColor) {
                if (selectedObjectId !== null) {
                    modifyObjColor(selectedObjectId, hexColor);
                }
                currentDrawColor = hexColor;
                var tbColor = document.getElementById('toolbarColorPicker');
                if (tbColor) tbColor.value = hexColor;
            };

            window.modifyObjColor = function(id, hexColor) {
                var obj = objectRegistry.find(function(o) { return o.id === id; });
                if (!obj) return;
                var rgb = hexToRgb(hexColor);
                obj.matArr = rgb;
                obj.colorHex = hexColor;
                obj.outArr = [Math.min(1.0, rgb[0] * 1.2), Math.min(1.0, rgb[1] * 1.2), Math.min(1.0, rgb[2] * 1.2)];
                
                var cesColor = new Cesium.Color(rgb[0], rgb[1], rgb[2], 1.0);
                var cesOut = new Cesium.Color(obj.outArr[0], obj.outArr[1], obj.outArr[2], 1.0);
                
                if (obj.type === 'box' && obj.entity.box) {
                    obj.entity.box.material = cesColor;
                    obj.entity.box.outlineColor = cesOut;
                } else if ((obj.type === 'cylinder' || obj.type === 'cone') && obj.entity.cylinder) {
                    obj.entity.cylinder.material = cesColor;
                    obj.entity.cylinder.outlineColor = cesOut;
                } else if (obj.type === 'sphere' && obj.entity.ellipsoid) {
                    obj.entity.ellipsoid.material = cesColor;
                    obj.entity.ellipsoid.outlineColor = cesOut;
                } else if (obj.type === 'polygon' && obj.entity.polygon) {
                    obj.entity.polygon.material = cesColor;
                    obj.entity.polygon.outlineColor = cesOut;
                }

                var inp = document.getElementById('ocbCustomColor');
                if (inp) inp.value = hexColor;

                reportStatus('LOG', 'Changed color of ' + obj.name + ' to ' + hexColor);
                syncDataToQt();
            };

            window.modifyObjDimensions = function(id, deltaSizeFactor, deltaHeight) {
                var obj = objectRegistry.find(function(o) { return o.id === id; });
                if (!obj) return;

                if (deltaHeight !== 0) {
                    obj.height = Math.max(2, Math.round((obj.height || 20) + deltaHeight));
                }

                if (deltaSizeFactor !== 1.0) {
                    if (obj.width) obj.width = Math.max(5, Math.round(obj.width * deltaSizeFactor));
                    if (obj.depth) obj.depth = Math.max(5, Math.round(obj.depth * deltaSizeFactor));
                    if (obj.radius) obj.radius = Math.max(3, Math.round(obj.radius * deltaSizeFactor));
                    if (obj.size) obj.size = Math.max(5, Math.round(obj.size * deltaSizeFactor));

                    if (obj.type === 'polygon' && obj.customPoints && obj.customPoints.length >= 3) {
                        var pts = obj.customPoints;
                        var sX = 0, sY = 0, sZ = 0;
                        for (var i = 0; i < pts.length; i++) {
                            sX += pts[i].x; sY += pts[i].y; sZ += pts[i].z;
                        }
                        var cX = sX / pts.length, cY = sY / pts.length, cZ = sZ / pts.length;
                        var newPts = [];
                        for (var i = 0; i < pts.length; i++) {
                            newPts.push(new Cesium.Cartesian3(
                                cX + (pts[i].x - cX) * deltaSizeFactor,
                                cY + (pts[i].y - cY) * deltaSizeFactor,
                                cZ + (pts[i].z - cZ) * deltaSizeFactor
                            ));
                        }
                        obj.customPoints = newPts;
                        obj.entity.polygon.hierarchy = new Cesium.PolygonHierarchy(newPts);
                    }
                }

                // อัปเดต Entity ของ Cesium
                if (obj.type === 'box' && obj.entity.box) {
                    obj.entity.box.dimensions = new Cesium.Cartesian3(obj.width, obj.depth, obj.height);
                    obj.entity.position = Cesium.Cartesian3.fromDegrees(obj.lon, obj.lat, obj.th + obj.height / 2);
                } else if ((obj.type === 'cylinder' || obj.type === 'cone') && obj.entity.cylinder) {
                    if (obj.type === 'cylinder') obj.entity.cylinder.topRadius = obj.radius;
                    obj.entity.cylinder.bottomRadius = obj.radius;
                    obj.entity.cylinder.length = obj.height;
                    obj.entity.position = Cesium.Cartesian3.fromDegrees(obj.lon, obj.lat, obj.th + obj.height / 2);
                } else if (obj.type === 'sphere' && obj.entity.ellipsoid) {
                    obj.entity.ellipsoid.radii = new Cesium.Cartesian3(obj.radius, obj.radius, obj.radius);
                    obj.entity.position = Cesium.Cartesian3.fromDegrees(obj.lon, obj.lat, obj.th + obj.radius);
                } else if (obj.type === 'polygon' && obj.entity.polygon) {
                    obj.entity.polygon.extrudedHeight = obj.th + obj.height;
                }

                if (selectedObjectId === id) openObjectControlBar(obj);
                reportStatus('LOG', 'Resized ' + obj.name + ': H=' + obj.height + 'm, Sz=' + (obj.width || obj.radius || obj.size) + 'm');
                syncDataToQt();
            };

            window.setActiveObjectHeight = function(val) {
                if (selectedObjectId !== null) {
                    setObjHeight(selectedObjectId, val);
                }
            };

            window.setObjHeight = function(id, val) {
                var obj = objectRegistry.find(function(o) { return o.id === id; });
                if (!obj) return;
                var h = parseFloat(val);
                if (isNaN(h) || h <= 0) {
                    var inp = document.getElementById('ocbHeightInput');
                    if (inp) inp.value = Math.round(obj.height || 20);
                    return;
                }
                h = Math.max(1, Math.round(h));
                obj.height = h;

                // อัปเดต Entity ของ Cesium ตามชนิดโมเดล 3D
                if (obj.type === 'box' && obj.entity && obj.entity.box) {
                    obj.entity.box.dimensions = new Cesium.Cartesian3(obj.width, obj.depth, obj.height);
                    obj.entity.position = Cesium.Cartesian3.fromDegrees(obj.lon, obj.lat, obj.th + obj.height / 2);
                } else if ((obj.type === 'cylinder' || obj.type === 'cone') && obj.entity && obj.entity.cylinder) {
                    if (obj.type === 'cylinder') obj.entity.cylinder.topRadius = obj.radius;
                    obj.entity.cylinder.bottomRadius = obj.radius;
                    obj.entity.cylinder.length = obj.height;
                    obj.entity.position = Cesium.Cartesian3.fromDegrees(obj.lon, obj.lat, obj.th + obj.height / 2);
                } else if (obj.type === 'sphere' && obj.entity && obj.entity.ellipsoid) {
                    obj.radius = Math.max(1, Math.round(obj.height / 2));
                    obj.entity.ellipsoid.radii = new Cesium.Cartesian3(obj.radius, obj.radius, obj.radius);
                    obj.entity.position = Cesium.Cartesian3.fromDegrees(obj.lon, obj.lat, obj.th + obj.radius);
                } else if (obj.type === 'polygon' && obj.entity && obj.entity.polygon) {
                    obj.entity.polygon.extrudedHeight = obj.th + obj.height;
                }

                if (selectedObjectId === id) {
                    var inp = document.getElementById('ocbHeightInput');
                    if (inp && document.activeElement !== inp) inp.value = obj.height;
                    var span = document.getElementById('ocbHeightVal');
                    if (span) span.textContent = obj.height + 'm';
                }
                reportStatus('LOG', 'Set height of ' + obj.name + ' to ' + obj.height + 'm');
                syncDataToQt();
            };

            function hlEntity(obj, on) {
                var hlMat = Cesium.Color.WHITE.withAlpha(0.35);
                var hlOut = Cesium.Color.WHITE;
                var mat = on ? hlMat : sColor(obj.matArr);
                var out = on ? hlOut : sColor(obj.outArr);

                if (obj.type === 'box' && obj.entity.box) {
                    obj.entity.box.material = mat; obj.entity.box.outlineColor = out;
                } else if ((obj.type === 'cylinder' || obj.type === 'cone') && obj.entity.cylinder) {
                    obj.entity.cylinder.material = mat; obj.entity.cylinder.outlineColor = out;
                } else if (obj.type === 'sphere' && obj.entity.ellipsoid) {
                    obj.entity.ellipsoid.material = mat; obj.entity.ellipsoid.outlineColor = out;
                } else if (obj.type === 'polygon' && obj.entity.polygon) {
                    obj.entity.polygon.material = mat; obj.entity.polygon.outlineColor = out;
                }
            }

            // =================================================================
            // DELETE OBJECT — ลบวัตถุ
            // =================================================================
            window.delObj = function(id) {
                var idx = objectRegistry.findIndex(function(o) { return o.id === id; });
                if (idx === -1) return;
                var obj = objectRegistry[idx];
                viewer.entities.remove(obj.entity);
                viewer.entities.remove(obj.lblEnt);
                objectRegistry.splice(idx, 1);
                if (selectedObjectId === id) selectedObjectId = null;
                refreshPanel();
                reportStatus('LOG', 'Deleted: ' + obj.name);
            };

            // =================================================================
            // EDIT FORM — แสดง/ซ่อน ฟอร์มแก้ไข
            // =================================================================
            window.showEdit = function(id) {
                var el = document.getElementById('ef-' + id);
                if (el) el.classList.toggle('vis');
            };

            window.applyEdit = function(id) {
                var obj = objectRegistry.find(function(o) { return o.id === id; });
                if (!obj) return;

                // อ่านค่าจาก Input
                var nm = document.getElementById('en-' + id);
                if (nm) obj.name = nm.value.trim() || obj.name;

                if (obj.type === 'box') {
                    var w = parseFloat((document.getElementById('ew-'+id)||{}).value); if (!isNaN(w) && w > 0) obj.width = w;
                    var d = parseFloat((document.getElementById('ed-'+id)||{}).value); if (!isNaN(d) && d > 0) obj.depth = d;
                    var h = parseFloat((document.getElementById('eh-'+id)||{}).value); if (!isNaN(h) && h > 0) obj.height = h;
                    obj.entity.box.dimensions = new Cesium.Cartesian3(obj.width, obj.depth, obj.height);
                    obj.entity.position = Cesium.Cartesian3.fromDegrees(obj.lon, obj.lat, obj.th + obj.height / 2);

                } else if (obj.type === 'cylinder') {
                    var r = parseFloat((document.getElementById('er-'+id)||{}).value); if (!isNaN(r) && r > 0) obj.radius = r;
                    var h = parseFloat((document.getElementById('eh-'+id)||{}).value); if (!isNaN(h) && h > 0) obj.height = h;
                    obj.entity.cylinder.topRadius = obj.radius;
                    obj.entity.cylinder.bottomRadius = obj.radius;
                    obj.entity.cylinder.length = obj.height;
                    obj.entity.position = Cesium.Cartesian3.fromDegrees(obj.lon, obj.lat, obj.th + obj.height / 2);

                } else if (obj.type === 'cone') {
                    var r = parseFloat((document.getElementById('er-'+id)||{}).value); if (!isNaN(r) && r > 0) obj.radius = r;
                    var h = parseFloat((document.getElementById('eh-'+id)||{}).value); if (!isNaN(h) && h > 0) obj.height = h;
                    obj.entity.cylinder.bottomRadius = obj.radius;
                    obj.entity.cylinder.length = obj.height;
                    obj.entity.position = Cesium.Cartesian3.fromDegrees(obj.lon, obj.lat, obj.th + obj.height / 2);

                } else if (obj.type === 'sphere') {
                    var r = parseFloat((document.getElementById('er-'+id)||{}).value); if (!isNaN(r) && r > 0) obj.radius = r;
                    obj.entity.ellipsoid.radii = new Cesium.Cartesian3(obj.radius, obj.radius, obj.radius);
                    obj.entity.position = Cesium.Cartesian3.fromDegrees(obj.lon, obj.lat, obj.th + obj.radius);

                } else if (obj.type === 'polygon') {
                    var h = parseFloat((document.getElementById('eh-'+id)||{}).value); if (!isNaN(h) && h > 0) obj.height = h;
                    obj.entity.polygon.extrudedHeight = obj.th + obj.height;
                }

                // อัปเดต Label
                var cfg = SCFG[obj.type];
                obj.lblEnt.label.text = cfg.icon + ' ' + obj.name;

                refreshPanel();
                reportStatus('LOG', 'Updated: ' + obj.name);
            };

            window.cancelEdit = function(id) {
                var el = document.getElementById('ef-' + id);
                if (el) el.classList.remove('vis');
            };

            // =================================================================
            // IMAGE OVERLAY SYSTEM — นำเข้ารูปภาพแนบไปตาม Terrain + Interactive Gizmo + HUD
            // =================================================================
            let imageRegistry = [];
            let nextImageId = 1;
            let selectedImageId = null;
            let imageGizmoEntities = [];
            let activeImageDrag = null;

            function clearImageGizmo() {
                for (var i = 0; i < imageGizmoEntities.length; i++) {
                    viewer.entities.remove(imageGizmoEntities[i]);
                }
                imageGizmoEntities = [];
            }

            function showImageGizmo(imgObj) {
                clearImageGizmo();
                if (!imgObj || imgObj.locked) return;

                function getHandleCartesian(dxM, dyM) {
                    var rotRad = Cesium.Math.toRadians(imgObj.rotation || 0);
                    var rotE = dxM * Math.cos(rotRad) - dyM * Math.sin(rotRad);
                    var rotN = dxM * Math.sin(rotRad) + dyM * Math.cos(rotRad);
                    var hLat = imgObj.lat + (rotN / 111320);
                    var hLon = imgObj.lon + (rotE / (111320 * Math.cos(imgObj.lat * Math.PI / 180)));
                    return Cesium.Cartesian3.fromDegrees(hLon, hLat, 0);
                }

                // 1. Center Handle (Move)
                var hMove = viewer.entities.add({
                    position: new Cesium.CallbackProperty(function() {
                        return Cesium.Cartesian3.fromDegrees(imgObj.lon, imgObj.lat, 0);
                    }, false),
                    point: {
                        pixelSize: 14, color: Cesium.Color.LIME,
                        outlineColor: Cesium.Color.WHITE, outlineWidth: 3,
                        disableDepthTestDistance: Number.POSITIVE_INFINITY
                    },
                    label: {
                        text: "✥ MOVE", font: "10px Consolas",
                        fillColor: Cesium.Color.WHITE, outlineColor: Cesium.Color.BLACK, outlineWidth: 2,
                        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                        pixelOffset: new Cesium.Cartesian2(0, 18),
                        disableDepthTestDistance: Number.POSITIVE_INFINITY
                    }
                });
                hMove._imgGizmo = { type: 'move', img: imgObj };
                imageGizmoEntities.push(hMove);

                // 2. Corner Handle (Scale / Resize by Hand)
                var hScale = viewer.entities.add({
                    position: new Cesium.CallbackProperty(function() {
                        var halfW = (imgObj.baseWidth * imgObj.scale) / 2;
                        var halfH = (imgObj.baseHeight * imgObj.scale) / 2;
                        return getHandleCartesian(halfW, -halfH);
                    }, false),
                    point: {
                        pixelSize: 16, color: Cesium.Color.ORANGE,
                        outlineColor: Cesium.Color.WHITE, outlineWidth: 3,
                        disableDepthTestDistance: Number.POSITIVE_INFINITY
                    },
                    label: {
                        text: "↔ RESIZE", font: "10px Consolas",
                        fillColor: Cesium.Color.WHITE, outlineColor: Cesium.Color.BLACK, outlineWidth: 2,
                        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                        pixelOffset: new Cesium.Cartesian2(25, 18),
                        disableDepthTestDistance: Number.POSITIVE_INFINITY
                    }
                });
                hScale._imgGizmo = { type: 'scale', img: imgObj };
                imageGizmoEntities.push(hScale);

                // 3. Top Handle (Rotate by Hand)
                var hRotate = viewer.entities.add({
                    position: new Cesium.CallbackProperty(function() {
                        var halfH = (imgObj.baseHeight * imgObj.scale) / 2;
                        return getHandleCartesian(0, halfH + 35);
                    }, false),
                    point: {
                        pixelSize: 16, color: Cesium.Color.CYAN,
                        outlineColor: Cesium.Color.WHITE, outlineWidth: 3,
                        disableDepthTestDistance: Number.POSITIVE_INFINITY
                    },
                    label: {
                        text: "🔄 ROTATE", font: "10px Consolas",
                        fillColor: Cesium.Color.WHITE, outlineColor: Cesium.Color.BLACK, outlineWidth: 2,
                        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                        pixelOffset: new Cesium.Cartesian2(0, -20),
                        disableDepthTestDistance: Number.POSITIVE_INFINITY
                    }
                });
                hRotate._imgGizmo = { type: 'rotate', img: imgObj };
                imageGizmoEntities.push(hRotate);
            }

            window.selectImage = function(id) {
                var img = imageRegistry.find(function(i) { return i.id === id; });
                if (img) {
                    selectedImageId = id;
                    showImageGizmo(img);
                    openImageControlBar(img);
                } else {
                    selectedImageId = null;
                    clearImageGizmo();
                    closeImageControlBar();
                }
            };

            function openImageControlBar(img) {
                var bar = document.getElementById('imageControlBar');
                if (!bar) return;
                bar.style.display = 'flex';
                document.getElementById('icbName').textContent = img.name;
                document.getElementById('icbOpacity').value = img.opacity !== undefined ? img.opacity : 0.85;
                document.getElementById('icbOpacityVal').textContent = Math.round((img.opacity !== undefined ? img.opacity : 0.85) * 100) + '%';
                document.getElementById('icbScale').value = img.scale || 1.0;
                document.getElementById('icbScaleVal').textContent = (img.scale || 1.0).toFixed(2) + 'x';
                document.getElementById('icbRotate').value = img.rotation || 0;
                document.getElementById('icbRotateVal').textContent = (img.rotation || 0) + '°';

                var lockBtn = document.getElementById('icbLockBtn');
                if (img.locked) {
                    lockBtn.textContent = '🔒 LOCKED (CLICK TO UNLOCK)';
                    lockBtn.classList.add('locked');
                } else {
                    lockBtn.textContent = '🔓 UNLOCKED (CLICK TO LOCK)';
                    lockBtn.classList.remove('locked');
                }
            }

            window.closeImageControlBar = function() {
                var bar = document.getElementById('imageControlBar');
                if (bar) bar.style.display = 'none';
            };

            window.setImageOpacity = function(val) {
                var item = imageRegistry.find(function(i) { return i.id === selectedImageId; });
                if (item) {
                    item.opacity = parseFloat(val);
                    document.getElementById('icbOpacityVal').textContent = Math.round(item.opacity * 100) + '%';
                }
            };

            window.setImageScaleSlider = function(val) {
                var item = imageRegistry.find(function(i) { return i.id === selectedImageId; });
                if (item) {
                    item.scale = parseFloat(val);
                    document.getElementById('icbScaleVal').textContent = item.scale.toFixed(2) + 'x';
                    syncDataToQt();
                }
            };

            window.stepImageScale = function(factor) {
                var item = imageRegistry.find(function(i) { return i.id === selectedImageId; });
                if (item) {
                    item.scale = Math.max(0.1, Math.min(10.0, item.scale * factor));
                    document.getElementById('icbScale').value = item.scale;
                    document.getElementById('icbScaleVal').textContent = item.scale.toFixed(2) + 'x';
                    syncDataToQt();
                }
            };

            window.setImageRotateSlider = function(val) {
                var item = imageRegistry.find(function(i) { return i.id === selectedImageId; });
                if (item) {
                    item.rotation = parseInt(val);
                    document.getElementById('icbRotateVal').textContent = item.rotation + '°';
                    syncDataToQt();
                }
            };

            window.stepImageRotate = function(deg) {
                var item = imageRegistry.find(function(i) { return i.id === selectedImageId; });
                if (item) {
                    var r = ((item.rotation || 0) + deg) % 360;
                    if (r < 0) r += 360;
                    item.rotation = Math.round(r);
                    document.getElementById('icbRotate').value = item.rotation;
                    document.getElementById('icbRotateVal').textContent = item.rotation + '°';
                    syncDataToQt();
                }
            };

            window.nudgeImage = function(dEastM, dNorthM) {
                var item = imageRegistry.find(function(i) { return i.id === selectedImageId; });
                if (item) {
                    item.lat += dNorthM / 111320;
                    item.lon += dEastM / (111320 * Math.cos(item.lat * Math.PI / 180));
                    syncDataToQt();
                }
            };

            window.toggleImageLock = function() {
                var item = imageRegistry.find(function(i) { return i.id === selectedImageId; });
                if (item) {
                    item.locked = !item.locked;
                    var lockBtn = document.getElementById('icbLockBtn');
                    if (item.locked) {
                        lockBtn.textContent = '🔒 LOCKED (CLICK TO UNLOCK)';
                        lockBtn.classList.add('locked');
                        clearImageGizmo();
                        reportStatus('LOG', 'Draft locked: ' + item.name + '. You can now trace polygons over it without moving the image.');
                    } else {
                        lockBtn.textContent = '🔓 UNLOCKED (CLICK TO LOCK)';
                        lockBtn.classList.remove('locked');
                        showImageGizmo(item);
                        reportStatus('LOG', 'Draft unlocked: ' + item.name);
                    }
                }
            };

            window.deleteActiveImage = function() {
                if (selectedImageId !== null) {
                    deleteImage(selectedImageId);
                    closeImageControlBar();
                }
            };

            window.handleImageUpload = function(e) {
                var file = e.target.files[0];
                if (!file) return;
                var reader = new FileReader();
                reader.onload = function(ev) {
                    var dataUrl = ev.target.result;
                    var img = new Image();
                    img.onload = function() {
                        var canvas = viewer.scene.canvas;
                        var centerCartesian = viewer.camera.pickEllipsoid(new Cesium.Cartesian2(canvas.clientWidth / 2, canvas.clientHeight / 2), viewer.scene.globe.ellipsoid);
                        var centerLat = 13.7563, centerLon = 100.5018;
                        if (centerCartesian) {
                            var c = Cesium.Cartographic.fromCartesian(centerCartesian);
                            centerLat = Cesium.Math.toDegrees(c.latitude);
                            centerLon = Cesium.Math.toDegrees(c.longitude);
                        } else {
                            var c = viewer.camera.positionCartographic;
                            centerLat = Cesium.Math.toDegrees(c.latitude);
                            centerLon = Cesium.Math.toDegrees(c.longitude);
                        }

                        var id = nextImageId++;
                        var name = "IMG_" + id + " (" + file.name + ")";
                        
                        var baseWidthMeters = 400;
                        var baseHeightMeters = baseWidthMeters * (img.naturalHeight / img.naturalWidth);
                        
                        var imgObj = {
                            id: id,
                            name: name,
                            dataUrl: dataUrl,
                            lat: centerLat,
                            lon: centerLon,
                            baseWidth: baseWidthMeters,
                            baseHeight: baseHeightMeters,
                            scale: 1.0,
                            rotation: 0,
                            opacity: 0.85,
                            locked: false,
                            entity: null
                        };

                        createImageEntity(imgObj);
                        imageRegistry.push(imgObj);
                        selectImage(id);
                        reportStatus("LOG", "Imported draft image: " + file.name + " (" + img.naturalWidth + "x" + img.naturalHeight + ")");
                        syncDataToQt();
                    };
                    img.src = dataUrl;
                };
                reader.readAsDataURL(file);
                e.target.value = "";
            };

            function createImageEntity(imgObj) {
                if (imgObj.entity) {
                    viewer.entities.remove(imgObj.entity);
                }

                imgObj.entity = viewer.entities.add({
                    name: imgObj.name,
                    rectangle: {
                        coordinates: new Cesium.CallbackProperty(function() {
                            var wM = imgObj.baseWidth * imgObj.scale;
                            var hM = imgObj.baseHeight * imgObj.scale;
                            var lDelta = (hM / 111320) / 2;
                            var lnDelta = (wM / (111320 * Math.cos(imgObj.lat * Math.PI / 180))) / 2;
                            return Cesium.Rectangle.fromDegrees(
                                imgObj.lon - lnDelta,
                                imgObj.lat - lDelta,
                                imgObj.lon + lnDelta,
                                imgObj.lat + lDelta
                            );
                        }, false),
                        rotation: new Cesium.CallbackProperty(function() {
                            return Cesium.Math.toRadians(imgObj.rotation || 0);
                        }, false),
                        stRotation: new Cesium.CallbackProperty(function() {
                            return Cesium.Math.toRadians(imgObj.rotation || 0);
                        }, false),
                        material: new Cesium.ImageMaterialProperty({
                            image: imgObj.dataUrl,
                            transparent: true,
                            color: new Cesium.CallbackProperty(function() {
                                var a = imgObj.opacity !== undefined ? imgObj.opacity : 0.85;
                                return Cesium.Color.WHITE.withAlpha(a);
                            }, false)
                        }),
                        classificationType: Cesium.ClassificationType.TERRAIN
                    }
                });
                imgObj.entity._imgId = imgObj.id;
            }

            window.scaleImage = function(id, factor) {
                var item = imageRegistry.find(function(i) { return i.id === id; });
                if (item) {
                    item.scale = Math.max(0.05, Math.min(50.0, item.scale * factor));
                    reportStatus("LOG", item.name + " scaled to " + item.scale.toFixed(2) + "x");
                    if (selectedImageId === id) openImageControlBar(item);
                    syncDataToQt();
                }
            };

            window.rotateImage = function(id, deltaDeg) {
                var item = imageRegistry.find(function(i) { return i.id === id; });
                if (item) {
                    var cur = item.rotation || 0;
                    var next = (cur + deltaDeg) % 360;
                    if (next < 0) next += 360;
                    item.rotation = Math.round(next);
                    reportStatus("LOG", item.name + " rotated to " + item.rotation + "°");
                    if (selectedImageId === id) openImageControlBar(item);
                    syncDataToQt();
                }
            };

            window.deleteImage = function(id) {
                var idx = imageRegistry.findIndex(function(i) { return i.id === id; });
                if (idx !== -1) {
                    var item = imageRegistry[idx];
                    if (item.entity) viewer.entities.remove(item.entity);
                    if (selectedImageId === id) {
                        clearImageGizmo();
                        closeImageControlBar();
                        selectedImageId = null;
                    }
                    imageRegistry.splice(idx, 1);
                    reportStatus("LOG", "Deleted image: " + item.name);
                    syncDataToQt();
                }
            };

            window.flyToImage = function(id) {
                var item = imageRegistry.find(function(i) { return i.id === id; });
                if (item && item.entity) {
                    selectImage(id);
                    viewer.flyTo(item.entity, { duration: 1.5 });
                }
            };

            function syncDataToQt() {
                var objs = objectRegistry.map(function(o) {
                    var polyPts = [];
                    if (o.type === 'polygon') {
                        var pts = o.customPoints;
                        if (!pts && o.entity && o.entity.polygon && o.entity.polygon.hierarchy) {
                            var hier = o.entity.polygon.hierarchy.getValue(Cesium.JulianDate.now());
                            if (hier && hier.positions) pts = hier.positions;
                        }
                        if (pts && pts.length > 0) {
                            for (var pIdx = 0; pIdx < pts.length; pIdx++) {
                                var c = Cesium.Cartographic.fromCartesian(pts[pIdx]);
                                polyPts.push({
                                    lat: Cesium.Math.toDegrees(c.latitude),
                                    lon: Cesium.Math.toDegrees(c.longitude),
                                    alt: c.height || 0
                                });
                            }
                        }
                    }
                    return {
                        id: o.id,
                        name: o.name,
                        type: o.type,
                        lat: o.lat,
                        lon: o.lon,
                        th: o.th || 0,
                        colorHex: o.colorHex || '#00E5FF',
                        width: Math.round(o.width || o.size || (o.radius ? o.radius*2 : 50)),
                        depth: Math.round(o.depth || o.size || (o.radius ? o.radius*2 : 50)),
                        radius: Math.round(o.radius || 25),
                        size: Math.round(o.size || o.width || (o.radius ? o.radius*2 : 50)),
                        height: Math.round(o.height || 25),
                        polyPts: polyPts
                    };
                });
                var imgs = imageRegistry.map(function(i) {
                    return {
                        id: i.id,
                        name: i.name,
                        scale: i.scale.toFixed(2),
                        rotation: (i.rotation || 0),
                        lat: i.lat.toFixed(4),
                        lon: i.lon.toFixed(4)
                    };
                });
                var pins = pinRegistry.map(function(p) {
                    return {
                        id: p.id,
                        label: p.label,
                        lat: p.lat.toFixed(4),
                        lon: p.lon.toFixed(4),
                        rRed: (Number.isInteger(Number(p.rRed)) ? Number(p.rRed) : Number(p.rRed).toFixed(1)),
                        rOrange: (Number.isInteger(Number(p.rOrange)) ? Number(p.rOrange) : Number(p.rOrange).toFixed(1)),
                        rYellow: (Number.isInteger(Number(p.rYellow)) ? Number(p.rYellow) : Number(p.rYellow).toFixed(1))
                    };
                });
                reportStatus("DATA_SYNC", JSON.stringify({ objects: objs, images: imgs, pins: pins }));
            }

            // =================================================================
            // PANEL RENDERING — ส่งข้อมูลให้ Qt
            // =================================================================
            function refreshPanel() {
                syncDataToQt();
            }



            // =================================================================
            // SEARCH & FLY — ค้นหาพิกัดแล้วบินไป
            // =================================================================
            window.searchAndFly = function() {
                var lat = parseFloat(document.getElementById('latInput').value);
                var lon = parseFloat(document.getElementById('lonInput').value);
                if (isNaN(lat) || isNaN(lon)) { reportStatus('ERROR', 'Invalid coordinates.'); return; }
                flyToCoords(lat, lon);
            };

            window.flyToCoords = function(lat, lon) {
                lat = parseFloat(lat); lon = parseFloat(lon);
                if (isNaN(lat) || isNaN(lon)) return;
                viewer.camera.flyTo({
                    destination: Cesium.Cartesian3.fromDegrees(lon, lat, 2000),
                    orientation: { heading: 0, pitch: Cesium.Math.toRadians(-50), roll: 0 },
                    duration: 1.5
                });
                reportStatus('LOG', 'Flying to ' + lat.toFixed(4) + ', ' + lon.toFixed(4));
            };

            // =================================================================
            // SPAWN FROM PYTHON — สร้างวัตถุจาก Python GUI
            // =================================================================
            window.spawnObjectAtCoords = function(shape, lat, lon, customName) {
                lat = parseFloat(lat); lon = parseFloat(lon);
                if (isNaN(lat) || isNaN(lon)) return;

                try {
                    Cesium.sampleTerrainMostDetailed(viewer.terrainProvider, [
                        Cesium.Cartographic.fromDegrees(lon, lat)
                    ]).then(function(samples) {
                        var h = (samples && samples[0]) ? (samples[0].height || 0) : 0;
                        buildObject(shape, lat, lon, h, 100);
                        if (customName) {
                            var last = objectRegistry[objectRegistry.length - 1];
                            last.name = customName;
                            last.lblEnt.label.text = SCFG[shape].icon + ' ' + customName;
                            refreshPanel();
                        }
                    }).catch(function() {
                        buildObject(shape, lat, lon, 0, 100);
                    });
                } catch(e) {
                    buildObject(shape, lat, lon, 0, 100);
                }
            };

            // =================================================================
            // CLEAR ALL — ลบวัตถุที่สร้างทั้งหมด (ไม่ยุ่ง Built-in)
            // =================================================================
            window.clearAllObjects = function() {
                for (var i = 0; i < objectRegistry.length; i++) {
                    viewer.entities.remove(objectRegistry[i].entity);
                    viewer.entities.remove(objectRegistry[i].lblEnt);
                }
                objectRegistry = [];
                selectedObjectId = null;
                nextObjId = 1;
                refreshPanel();
                reportStatus('LOG', 'All custom objects cleared.');
            };

            // Init panel
            refreshPanel();
            reportStatus('SUCCESS', 'Interactive 3D Edit Mode Engine Active.');

        } catch (err) {
            reportStatus('ERROR', 'Init Crash: ' + err.message);
        }
    </script>
</body>
</html>
"""

# =========================================================================
# 2. Local HTTP Server — ส่ง HTML/JS ไปยัง QWebEngineView
# =========================================================================
class DiagnosticHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(HTML_MAP_CODE_3D.encode('utf-8'))

    def log_message(self, format, *args):
        pass

def run_auto_port_server():
    server = socketserver.TCPServer(("127.0.0.1", 0), DiagnosticHTTPHandler)
    allocated_port = server.server_address[1]
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    return allocated_port

# =========================================================================
# 2.5 3D MESH GENERATOR & EXPORTER (.OBJ / .STL) FOR OPENFOAM & CFD
# =========================================================================
def fetch_surrounding_osm_buildings(center_lat, center_lon, radius_meters=300.0, default_height=8.0, center_th=0.0):
    try:
        deg_lat = radius_meters / 111320.0
        cos_lat = math.cos(math.radians(center_lat))
        deg_lon = radius_meters / (111320.0 * (cos_lat if cos_lat > 0.01 else 1.0))

        min_lat = center_lat - deg_lat
        max_lat = center_lat + deg_lat
        min_lon = center_lon - deg_lon
        max_lon = center_lon + deg_lon

        query = f'[out:json][timeout:12];(way["building"]({min_lat:.5f},{min_lon:.5f},{max_lat:.5f},{max_lon:.5f}););out body;>;out skel qt;'
        url = 'https://overpass-api.de/api/interpreter'
        req = urllib.request.Request(url, data=query.encode('utf-8'), headers={'User-Agent': 'CesiumCFDExport/1.0'})

        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            nodes = {e['id']: (e['lat'], e['lon']) for e in data.get('elements', []) if e.get('type') == 'node'}
            ways = [e for e in data.get('elements', []) if e.get('type') == 'way']

        osm_objs = []
        for idx, w in enumerate(ways, 1):
            w_nodes = [nodes[nid] for nid in w.get('nodes', []) if nid in nodes]
            if len(w_nodes) >= 3:
                if w_nodes[0] == w_nodes[-1]:
                    w_nodes = w_nodes[:-1]
                tags = w.get('tags', {})
                h_str = tags.get('height') or tags.get('building:height')
                lvl_str = tags.get('building:levels')
                h = None
                try:
                    if h_str:
                        h = float(str(h_str).lower().replace('m', '').strip())
                    elif lvl_str:
                        h = float(str(lvl_str).strip()) * 3.0
                except:
                    h = None

                if h is None or h <= 0:
                    # ค่ามาตรฐานตามต้นฉบับของ Cesium OSM Buildings
                    b_type = tags.get('building', '').lower()
                    if b_type in ('apartments', 'office', 'commercial', 'hotel', 'hospital', 'school'):
                        h = 10.0
                    elif b_type in ('industrial', 'warehouse'):
                        h = 7.0
                    elif b_type in ('garage', 'shed', 'hut'):
                        h = 3.5
                    else:
                        area_m2 = 0.0
                        if len(w_nodes) >= 3:
                            for k in range(len(w_nodes)):
                                knxt = (k + 1) % len(w_nodes)
                                x1 = (w_nodes[k][1] - center_lon) * 111320.0 * math.cos(math.radians(center_lat))
                                y1 = (w_nodes[k][0] - center_lat) * 111320.0
                                x2 = (w_nodes[knxt][1] - center_lon) * 111320.0 * math.cos(math.radians(center_lat))
                                y2 = (w_nodes[knxt][0] - center_lat) * 111320.0
                                area_m2 += (x1 * y2 - x2 * y1)
                            area_m2 = abs(area_m2) * 0.5
                        if area_m2 > 400:
                            h = 7.5
                        elif area_m2 > 150:
                            h = 5.5
                        else:
                            h = 4.5

                b_name = tags.get('name') or f"CESIUM_OSM_{idx}"
                b_name = b_name.replace(" ", "_").replace("'", "").replace('"', '')

                osm_objs.append({
                    'id': f"OSM_{w['id']}",
                    'name': b_name,
                    'type': 'polygon',
                    'lat': sum(p[0] for p in w_nodes) / len(w_nodes),
                    'lon': sum(p[1] for p in w_nodes) / len(w_nodes),
                    'th': center_th,
                    'height': h,
                    'colorHex': '#D4D4D8',
                    'polyPts': [{'lat': p[0], 'lon': p[1], 'alt': center_th} for p in w_nodes]
                })
        return osm_objs
    except Exception as e:
        print(f"Warning: Failed to fetch OSM buildings: {e}")
        return []

def compute_face_normal(v1, v2, v3):
    ax, ay, az = v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]
    bx, by, bz = v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]
    nx = ay * bz - az * by
    ny = az * bx - ax * bz
    nz = ax * by - ay * bx
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length > 1e-9:
        return (nx / length, ny / length, nz / length)
    return (0.0, 0.0, 1.0)

def build_3d_mesh_groups(selected_objects, include_ground=True, ground_margin=50.0):
    if not selected_objects:
        return []

    lat0 = sum(float(o.get('lat', 0.0)) for o in selected_objects) / len(selected_objects)
    lon0 = sum(float(o.get('lon', 0.0)) for o in selected_objects) / len(selected_objects)
    alt0 = min(float(o.get('th', 0.0)) for o in selected_objects)

    def to_enu(lat, lon, alt):
        x = (float(lon) - lon0) * (math.pi / 180.0) * 6378137.0 * math.cos(math.radians(lat0))
        y = (float(lat) - lat0) * (math.pi / 180.0) * 6356752.3
        z = float(alt) - alt0
        return x, y, z

    groups = []
    all_xy_coords = []

    for obj in selected_objects:
        shape_type = str(obj.get('type', 'box')).lower()
        name = str(obj.get('name', f"OBJ_{obj.get('id', 0)}")).replace(" ", "_")
        lat = float(obj.get('lat', lat0))
        lon = float(obj.get('lon', lon0))
        th = float(obj.get('th', alt0))
        h = float(obj.get('height', 20.0))
        cx, cy, base_z = to_enu(lat, lon, th)
        top_z = base_z + h
        triangles = []

        if shape_type == 'polygon':
            poly_pts = obj.get('polyPts', [])
            if poly_pts and len(poly_pts) >= 3:
                pts_2d = [to_enu(p['lat'], p['lon'], th)[:2] for p in poly_pts]
            else:
                sz = float(obj.get('size', 20.0))
                pts_2d = [
                    (cx - sz/2, cy - sz/2),
                    (cx + sz/2, cy - sz/2),
                    (cx + sz*0.7, cy),
                    (cx + sz/2, cy + sz/2),
                    (cx - sz/2, cy + sz/2),
                    (cx - sz*0.7, cy)
                ]
            all_xy_coords.extend(pts_2d)
            n = len(pts_2d)
            mid_x = sum(p[0] for p in pts_2d) / n
            mid_y = sum(p[1] for p in pts_2d) / n

            # Bottom cap
            for i in range(n):
                nxt = (i + 1) % n
                triangles.append(((mid_x, mid_y, base_z), (pts_2d[nxt][0], pts_2d[nxt][1], base_z), (pts_2d[i][0], pts_2d[i][1], base_z)))

            # Top cap
            for i in range(n):
                nxt = (i + 1) % n
                triangles.append(((mid_x, mid_y, top_z), (pts_2d[i][0], pts_2d[i][1], top_z), (pts_2d[nxt][0], pts_2d[nxt][1], top_z)))

            # Side walls
            for i in range(n):
                nxt = (i + 1) % n
                b1 = (pts_2d[i][0], pts_2d[i][1], base_z)
                b2 = (pts_2d[nxt][0], pts_2d[nxt][1], base_z)
                t1 = (pts_2d[i][0], pts_2d[i][1], top_z)
                t2 = (pts_2d[nxt][0], pts_2d[nxt][1], top_z)
                triangles.append((b1, b2, t2))
                triangles.append((b1, t2, t1))

        elif shape_type == 'box':
            w = float(obj.get('width', obj.get('size', 20.0)))
            d = float(obj.get('depth', obj.get('size', 20.0)))
            hw, hd = w / 2.0, d / 2.0
            x0, x1 = cx - hw, cx + hw
            y0, y1 = cy - hd, cy + hd
            all_xy_coords.extend([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])

            v0 = (x0, y0, base_z); v1 = (x1, y0, base_z)
            v2 = (x1, y1, base_z); v3 = (x0, y1, base_z)
            v4 = (x0, y0, top_z);  v5 = (x1, y0, top_z)
            v6 = (x1, y1, top_z);  v7 = (x0, y1, top_z)

            # Bottom (-Z)
            triangles.append((v0, v2, v1))
            triangles.append((v0, v3, v2))
            # Top (+Z)
            triangles.append((v4, v5, v6))
            triangles.append((v4, v6, v7))
            # Front (-Y)
            triangles.append((v0, v1, v5))
            triangles.append((v0, v5, v4))
            # Right (+X)
            triangles.append((v1, v2, v6))
            triangles.append((v1, v6, v5))
            # Back (+Y)
            triangles.append((v2, v3, v7))
            triangles.append((v2, v7, v6))
            # Left (-X)
            triangles.append((v3, v0, v4))
            triangles.append((v3, v4, v7))

        elif shape_type == 'cylinder':
            r = float(obj.get('radius', obj.get('size', 20.0) / 2.0))
            seg = 24
            pts_bot, pts_top = [], []
            for i in range(seg):
                ang = 2.0 * math.pi * i / seg
                px = cx + r * math.cos(ang)
                py = cy + r * math.sin(ang)
                pts_bot.append((px, py, base_z))
                pts_top.append((px, py, top_z))
                all_xy_coords.append((px, py))
            c_bot = (cx, cy, base_z)
            c_top = (cx, cy, top_z)

            for i in range(seg):
                nxt = (i + 1) % seg
                triangles.append((c_bot, pts_bot[nxt], pts_bot[i]))
                triangles.append((c_top, pts_top[i], pts_top[nxt]))
                triangles.append((pts_bot[i], pts_bot[nxt], pts_top[nxt]))
                triangles.append((pts_bot[i], pts_top[nxt], pts_top[i]))

        elif shape_type == 'cone':
            r = float(obj.get('radius', obj.get('size', 20.0) / 2.0))
            seg = 24
            pts_bot = []
            for i in range(seg):
                ang = 2.0 * math.pi * i / seg
                px = cx + r * math.cos(ang)
                py = cy + r * math.sin(ang)
                pts_bot.append((px, py, base_z))
                all_xy_coords.append((px, py))
            c_bot = (cx, cy, base_z)
            apex = (cx, cy, top_z)

            for i in range(seg):
                nxt = (i + 1) % seg
                triangles.append((c_bot, pts_bot[nxt], pts_bot[i]))
                triangles.append((pts_bot[i], pts_bot[nxt], apex))

        elif shape_type == 'sphere':
            r = float(obj.get('radius', obj.get('size', 20.0) / 2.0))
            scz = base_z + r
            lat_seg = 12
            lon_seg = 16
            sphere_pts = []
            for i in range(lat_seg + 1):
                theta = math.pi * i / lat_seg
                sin_t = math.sin(theta)
                cos_t = math.cos(theta)
                ring = []
                for j in range(lon_seg + 1):
                    phi = 2.0 * math.pi * j / lon_seg
                    px = cx + r * sin_t * math.cos(phi)
                    py = cy + r * sin_t * math.sin(phi)
                    pz = scz + r * cos_t
                    ring.append((px, py, pz))
                    all_xy_coords.append((px, py))
                sphere_pts.append(ring)

            for i in range(lat_seg):
                for j in range(lon_seg):
                    p1 = sphere_pts[i][j]
                    p2 = sphere_pts[i+1][j]
                    p3 = sphere_pts[i+1][j+1]
                    p4 = sphere_pts[i][j+1]
                    if i > 0:
                        triangles.append((p1, p2, p4))
                    if i < lat_seg - 1:
                        triangles.append((p2, p3, p4))

        groups.append({'name': name, 'triangles': triangles})

    # Ground Baseplate (Boundary Patch for OpenFOAM/CFD)
    if include_ground and all_xy_coords:
        min_x = min(p[0] for p in all_xy_coords) - ground_margin
        max_x = max(p[0] for p in all_xy_coords) + ground_margin
        min_y = min(p[1] for p in all_xy_coords) - ground_margin
        max_y = max(p[1] for p in all_xy_coords) + ground_margin
        gz = 0.0

        gp0 = (min_x, min_y, gz)
        gp1 = (max_x, min_y, gz)
        gp2 = (max_x, max_y, gz)
        gp3 = (min_x, max_y, gz)

        ground_triangles = [
            (gp0, gp1, gp2),
            (gp0, gp2, gp3)
        ]
        groups.insert(0, {'name': 'Ground_Terrain', 'triangles': ground_triangles})

    return groups

def write_obj_file(filepath, groups):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("# Wavefront OBJ exported by Cesium 3D Platform\n")
        f.write("# Unit: Meters (Local ENU Cartesian Frame)\n")
        f.write("# Compatible with OpenFOAM snappyHexMesh, Blender, CAD\n\n")

        v_offset = 1
        for grp in groups:
            name = grp['name']
            f.write(f"o {name}\n")
            triangles = grp['triangles']
            for tri in triangles:
                for v in tri:
                    f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
            for i in range(len(triangles)):
                idx = v_offset + i * 3
                f.write(f"f {idx} {idx+1} {idx+2}\n")
            v_offset += len(triangles) * 3
            f.write("\n")

def write_stl_file(filepath, groups):
    with open(filepath, 'w', encoding='utf-8') as f:
        for grp in groups:
            name = grp['name']
            f.write(f"solid {name}\n")
            for tri in grp['triangles']:
                norm = compute_face_normal(tri[0], tri[1], tri[2])
                f.write(f"  facet normal {norm[0]:.6e} {norm[1]:.6e} {norm[2]:.6e}\n")
                f.write("    outer loop\n")
                f.write(f"      vertex {tri[0][0]:.4f} {tri[0][1]:.4f} {tri[0][2]:.4f}\n")
                f.write(f"      vertex {tri[1][0]:.4f} {tri[1][1]:.4f} {tri[1][2]:.4f}\n")
                f.write(f"      vertex {tri[2][0]:.4f} {tri[2][1]:.4f} {tri[2][2]:.4f}\n")
                f.write("    endloop\n")
                f.write("  endfacet\n")
            f.write(f"endsolid {name}\n")

class Export3DDialog(QDialog):
    def __init__(self, parent, objects):
        super().__init__(parent)
        self.setWindowTitle("📤 Export 3D Models (.OBJ / .STL) for OpenFOAM & CAD")
        self.resize(560, 520)
        self.objects = objects

        self.setStyleSheet("""
            QDialog { background-color: #0A0F0D; color: #E0FFE8; font-family: 'Consolas', monospace; }
            QLabel { color: #A8FFB8; font-size: 11px; }
            QGroupBox {
                border: 1px solid #00AA55; border-radius: 6px; margin-top: 12px;
                font-weight: bold; color: #00FF66; padding-top: 14px; font-size: 12px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
            QPushButton {
                background-color: #005533; color: #FFF; border: 1px solid #00AA55;
                border-radius: 4px; padding: 6px 12px; font-weight: bold; font-family: 'Consolas', monospace;
            }
            QPushButton:hover { background-color: #008844; border-color: #00FF66; }
            QListWidget {
                background-color: #020604; border: 1px solid #007744; border-radius: 4px;
                color: #E0FFE8; font-family: 'Consolas', monospace; font-size: 11px;
            }
            QListWidget::item { padding: 4px 6px; }
            QListWidget::item:hover { background-color: #003318; }
            QRadioButton, QCheckBox { color: #E0FFE8; font-size: 11px; }
            QSpinBox {
                background-color: #020604; color: #FFF; border: 1px solid #00AA55;
                padding: 4px 8px; border-radius: 4px; font-family: 'Consolas', monospace;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header Info Banner
        info_banner = QLabel("📐 <b>Metric ENU Coordinates (Meters) centered at (0, 0, 0)</b><br>"
                             "<font color='#38BDF8'>Preserves real-world distances between objects for OpenFOAM CFD, Blender, and CAD.</font>")
        info_banner.setStyleSheet("background: rgba(0, 50, 30, 0.5); border: 1px solid rgba(0, 255, 102, 0.3); padding: 8px; border-radius: 4px;")
        layout.addWidget(info_banner)

        # 1. Object Selection List
        obj_grp = QGroupBox("1. Select 3D Models to Export:")
        obj_layout = QVBoxLayout(obj_grp)
        obj_layout.setSpacing(6)

        sel_btn_row = QHBoxLayout()
        sel_all_b = QPushButton("Select All")
        sel_all_b.setStyleSheet("background: #004422; padding: 3px 8px; font-size: 10px;")
        sel_all_b.clicked.connect(self.select_all_objects)
        sel_btn_row.addWidget(sel_all_b)

        desel_all_b = QPushButton("Deselect All")
        desel_all_b.setStyleSheet("background: #442222; padding: 3px 8px; font-size: 10px;")
        desel_all_b.clicked.connect(self.deselect_all_objects)
        sel_btn_row.addWidget(desel_all_b)
        sel_btn_row.addStretch()
        obj_layout.addLayout(sel_btn_row)

        self.obj_checklist = QListWidget()
        self.item_checkboxes = []
        for obj in self.objects:
            item = QListWidgetItem()
            cb = QCheckBox(f"{obj['name']} ({obj['type'].upper()}) - Height: {obj['height']}m")
            cb.setChecked(True)
            self.obj_checklist.addItem(item)
            self.obj_checklist.setItemWidget(item, cb)
            self.item_checkboxes.append((cb, obj))
        obj_layout.addWidget(self.obj_checklist)
        layout.addWidget(obj_grp)

        # 2. Ground Baseplate Settings
        ground_grp = QGroupBox("2. Ground Baseplate (พื้นผิวสำหรับ OpenFOAM/CFD):")
        ground_layout = QVBoxLayout(ground_grp)
        self.ground_cb = QCheckBox("สร้างแผ่นพื้นผิว Ground Plane (Z = 0) อัตโนมัติ (Boundary: 'Ground_Terrain')")
        self.ground_cb.setChecked(True)
        ground_layout.addWidget(self.ground_cb)

        margin_row = QHBoxLayout()
        margin_row.addWidget(QLabel("ระยะขอบรอบอาคาร (Margin / Padding):"))
        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(5, 2000)
        self.margin_spin.setValue(50)
        self.margin_spin.setSuffix(" m")
        margin_row.addWidget(self.margin_spin)
        margin_row.addStretch()
        ground_layout.addLayout(margin_row)
        layout.addWidget(ground_grp)

        # 3. Cesium OSM 3D Buildings in Area
        cesium_grp = QGroupBox("3. Cesium OSM 3D Buildings (โมเดลอาคาร 3D เดิมของ Cesium ในพื้นที่):")
        cesium_layout = QVBoxLayout(cesium_grp)
        self.cesium_osm_cb = QCheckBox("Export โมเดลอาคาร 3D เดิมของ Cesium ในบริเวณรอบๆ ด้วย (Cesium OSM Buildings)")
        self.cesium_osm_cb.setChecked(True)
        cesium_layout.addWidget(self.cesium_osm_cb)

        cesium_cfg_row = QHBoxLayout()
        cesium_cfg_row.addWidget(QLabel("รัศมีพื้นที่รอบโมเดล (Search Radius):"))
        self.osm_radius_spin = QSpinBox()
        self.osm_radius_spin.setRange(50, 3000)
        self.osm_radius_spin.setValue(300)
        self.osm_radius_spin.setSuffix(" m")
        cesium_cfg_row.addWidget(self.osm_radius_spin)
        cesium_cfg_row.addStretch()
        cesium_layout.addLayout(cesium_cfg_row)

        osm_note = QLabel("<font color='#38BDF8'>ℹ️ ความสูงอาคารและรูปทรงจะใช้ค่าตามต้นฉบับของ Cesium (คำนวณอัตโนมัติจากข้อมูลความสูง จำนวนชั้น และขนาดพื้นที่อาคาร)</font>")
        osm_note.setStyleSheet("font-size: 10px;")
        cesium_layout.addWidget(osm_note)
        layout.addWidget(cesium_grp)

        # 4. Export Format
        fmt_grp = QGroupBox("4. Export File Format:")
        fmt_layout = QHBoxLayout(fmt_grp)
        self.rb_obj = QRadioButton("Wavefront OBJ (.obj)")
        self.rb_stl = QRadioButton("StereoLithography (.stl)")
        self.rb_both = QRadioButton("Both Formats (.obj + .stl)")
        self.rb_both.setChecked(True)

        self.fmt_group = QButtonGroup(self)
        self.fmt_group.addButton(self.rb_obj, 1)
        self.fmt_group.addButton(self.rb_stl, 2)
        self.fmt_group.addButton(self.rb_both, 3)

        fmt_layout.addWidget(self.rb_obj)
        fmt_layout.addWidget(self.rb_stl)
        fmt_layout.addWidget(self.rb_both)
        layout.addWidget(fmt_grp)

        # 4. Action Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_b = QPushButton("Cancel")
        cancel_b.setStyleSheet("background: #333333; color: #AAA; border-color: #555;")
        cancel_b.clicked.connect(self.reject)
        btn_row.addWidget(cancel_b)

        export_b = QPushButton("💾 EXPORT & SAVE FILE...")
        export_b.setStyleSheet("background: #00AA55; color: #000; font-weight: bold; padding: 7px 18px;")
        export_b.clicked.connect(self.do_export)
        btn_row.addWidget(export_b)
        layout.addLayout(btn_row)

    def select_all_objects(self):
        for cb, _ in self.item_checkboxes:
            cb.setChecked(True)

    def deselect_all_objects(self):
        for cb, _ in self.item_checkboxes:
            cb.setChecked(False)

    def do_export(self):
        selected = [obj for cb, obj in self.item_checkboxes if cb.isChecked()]
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one 3D object to export.")
            return

        fmt_id = self.fmt_group.checkedId()
        if fmt_id == 1:
            file_filter = "Wavefront OBJ (*.obj)"
            default_ext = ".obj"
        elif fmt_id == 2:
            file_filter = "StereoLithography STL (*.stl)"
            default_ext = ".stl"
        else:
            file_filter = "3D Files (*.obj *.stl);;Wavefront OBJ (*.obj);;StereoLithography STL (*.stl)"
            default_ext = ".obj"

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Exported 3D Model", "cesium_model" + default_ext, file_filter
        )
        if not filepath:
            return

        base_path, _ = os.path.splitext(filepath)
        include_ground = self.ground_cb.isChecked()
        margin = float(self.margin_spin.value())

        # Check if user wants surrounding Cesium OSM buildings
        osm_buildings = []
        if self.cesium_osm_cb.isChecked():
            c_lat = sum(float(o.get('lat', 0.0)) for o in selected) / len(selected)
            c_lon = sum(float(o.get('lon', 0.0)) for o in selected) / len(selected)
            c_th = min(float(o.get('th', 0.0)) for o in selected)
            r_meters = float(self.osm_radius_spin.value())
            osm_buildings = fetch_surrounding_osm_buildings(c_lat, c_lon, r_meters, center_th=c_th)

        all_to_export = selected + osm_buildings

        # Build 3D mesh
        mesh_groups = build_3d_mesh_groups(all_to_export, include_ground=include_ground, ground_margin=margin)
        total_triangles = sum(len(g['triangles']) for g in mesh_groups)

        saved_files = []
        try:
            if fmt_id in (1, 3):
                obj_path = base_path + ".obj"
                write_obj_file(obj_path, mesh_groups)
                saved_files.append(obj_path)

            if fmt_id in (2, 3):
                stl_path = base_path + ".stl"
                write_stl_file(stl_path, mesh_groups)
                saved_files.append(stl_path)

            msg = (
                f"<b>✅ 3D Model Exported Successfully!</b><br><br>"
                f"<b>Files Created:</b><br>" + "<br>".join(f"• {f}" for f in saved_files) + "<br><br>"
                f"<b>Statistics:</b><br>"
                f"• Custom Objects: {len(selected)}<br>"
                f"• Cesium OSM Buildings: {len(osm_buildings)}<br>"
                f"• Total Exported Solids: {len(mesh_groups)}<br>"
                f"• Total Triangles: {total_triangles:,}<br>"
                f"• Ground Baseplate: {'Included (Z=0)' if include_ground else 'No'}<br>"
                f"• Coordinate System: Metric ENU (Meters, centered at (0, 0, 0))<br><br>"
                f"<font color='#38BDF8'>Ready to import into OpenFOAM (snappyHexMesh), Blender, or CAD!</font>"
            )
            QMessageBox.information(self, "Export Complete", msg)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"An error occurred while saving files:\n{str(e)}")

# =========================================================================
# 3. PySide6 GUI — หน้าต่างแอปพลิเคชันหลัก (Python side controls)
# =========================================================================
class Cesium3DIsolatedConsole(QMainWindow):
    def __init__(self, target_port):
        super().__init__()
        self.setWindowTitle("🔴 CESIUM 3D INTERACTIVE EDIT MODE ENGINE")
        self.resize(1400, 900)
        self.target_port = target_port
        self.edit_mode = False

        self.setStyleSheet("""
            QWidget { background-color: #0A0F0D; color: #A8FFB8; font-family: 'Consolas', monospace; }
            QLineEdit {
                background-color: #020604; border: 1px solid #00AA55; color: #38BDF8;
                padding: 5px 8px; font-family: 'Consolas', monospace; font-size: 12px; border-radius: 4px;
            }
            QLineEdit:focus { border-color: #00FF66; }
            QComboBox {
                background-color: #020604; border: 1px solid #00AA55; color: #00FF66;
                padding: 5px 8px; font-family: 'Consolas', monospace; font-size: 12px; border-radius: 4px;
            }
            QComboBox QAbstractItemView { background-color: #0A0F0D; color: #00FF66; selection-background-color: #00AA55; }
            QPushButton {
                background-color: #00AA55; color: #000000; border: none; font-weight: bold;
                padding: 6px 12px; border-radius: 4px; font-family: 'Consolas', monospace;
            }
            QPushButton:hover { background-color: #00FF66; }
            QPushButton:checked { background-color: #00FF66; color: #000; }
            QTextEdit { background-color: #020604; border: 1px solid #00AA55; color: #38BDF8; font-size: 12px; }
            QLabel { font-weight: bold; color: #00FF66; font-size: 13px; }
        """)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        self.main_layout = layout
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 🌐 Web View (3D Viewport)
        layout.addWidget(QLabel("🌐 3D INTERACTIVE VIEWPORT (WITH CESIUM EDIT ENGINE):"))
        self.web_view = QWebEngineView()
        self.web_view.titleChanged.connect(self.capture_js_logs)
        layout.addWidget(self.web_view, 7)

        # 🎛️ Bottom Section: Split between Log and Object Data Panel
        bottom_container = QWidget()
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)

        # Left Column: Kernel Debuglog
        log_box = QWidget()
        log_layout = QVBoxLayout(log_box)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(4)
        log_layout.addWidget(QLabel("📟 KERNEL DEBUGLOG:"))
        self.debug_log = QTextEdit()
        self.debug_log.setReadOnly(True)
        log_layout.addWidget(self.debug_log)
        bottom_layout.addWidget(log_box, 5)

        # Right Column: Objects & Image Overlays Panel
        panel_box = QWidget()
        panel_layout = QVBoxLayout(panel_box)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(4)
        
        # Header Row with Title (Only one export button kept on the top toolbar)
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.addWidget(QLabel("📋 OBJECT & OVERLAY DATA:"))
        header_row.addStretch()
        panel_layout.addLayout(header_row)

        self.data_tabs = QTabWidget()
        self.data_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #00AA55; background: #020604; }
            QTabBar::tab { background: #0A0F0D; color: #A8FFB8; padding: 6px 12px; font-weight: bold; }
            QTabBar::tab:selected { background: #00AA55; color: #000; }
        """)

        # Tab 1: 3D Objects
        self.obj_list_widget = QListWidget()
        self.obj_list_widget.setStyleSheet("background: #020604; border: none; color: #A8FFB8;")
        self.data_tabs.addTab(self.obj_list_widget, "🏢 Objects (0)")

        # Tab 2: Image Overlays
        self.img_list_widget = QListWidget()
        self.img_list_widget.setStyleSheet("background: #020604; border: none; color: #A8FFB8;")
        self.data_tabs.addTab(self.img_list_widget, "🖼️ Images (0)")

        # Tab 3: Tactical Pins
        self.pin_list_widget = QListWidget()
        self.pin_list_widget.setStyleSheet("background: #020604; border: none; color: #A8FFB8;")
        self.data_tabs.addTab(self.pin_list_widget, "🎯 Pins (0)")

        panel_layout.addWidget(self.data_tabs)
        bottom_layout.addWidget(panel_box, 5)

        # 🔽 / 🔼 Collapse/Expand Toggle Bar for Bottom Panel
        toggle_bar = QHBoxLayout()
        toggle_bar.setContentsMargins(0, 0, 0, 0)
        toggle_bar.setSpacing(6)

        sep_left = QFrame()
        sep_left.setFrameShape(QFrame.HLine)
        sep_left.setStyleSheet("border: none; border-top: 1px solid rgba(0, 255, 102, 0.25);")

        self.toggle_bottom_btn = QPushButton("▼ HIDE PANEL (กดเพื่อซ่อนแผงด้านล่าง)")
        self.toggle_bottom_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_bottom_btn.setToolTip("คลิกเพื่อ ยุบ/ขยาย แผงบันทึกข้อความและข้อมูลวัตถุ (กด F12 เพื่อสลับได้)")
        self.toggle_bottom_btn.setShortcut("F12")
        self.toggle_bottom_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(6, 18, 12, 0.9); color: #00FF66;
                border: 1px solid rgba(0, 255, 102, 0.4); border-radius: 4px;
                padding: 3px 18px; font-weight: bold; font-size: 11px;
                font-family: 'Consolas', monospace;
            }
            QPushButton:hover {
                background-color: #00AA55; color: #000000;
                border-color: #00FF66;
            }
        """)
        self.toggle_bottom_btn.clicked.connect(self.toggle_bottom_panel)

        sep_right = QFrame()
        sep_right.setFrameShape(QFrame.HLine)
        sep_right.setStyleSheet("border: none; border-top: 1px solid rgba(0, 255, 102, 0.25);")

        toggle_bar.addWidget(sep_left, 1)
        toggle_bar.addWidget(self.toggle_bottom_btn, 0)
        toggle_bar.addWidget(sep_right, 1)

        layout.addLayout(toggle_bar)

        self.bottom_container = bottom_container
        layout.addWidget(self.bottom_container, 3)

        self.web_view.setUrl(QUrl(f"http://127.0.0.1:{self.target_port}/"))

    def toggle_bottom_panel(self):
        is_visible = self.bottom_container.isVisible()
        if is_visible:
            self.bottom_container.hide()
            self.toggle_bottom_btn.setText("▲ SHOW PANEL (กดเพื่อแสดงแผงด้านล่าง)")
            self.toggle_bottom_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(0, 100, 50, 0.85); color: #E0FFE8;
                    border: 1px solid #00FF66; border-radius: 4px;
                    padding: 4px 18px; font-weight: bold; font-size: 11px;
                    font-family: 'Consolas', monospace;
                }
                QPushButton:hover {
                    background-color: #00FF66; color: #000000;
                }
            """)
            self.main_layout.setStretch(1, 1)
        else:
            self.bottom_container.show()
            self.toggle_bottom_btn.setText("▼ HIDE PANEL (กดเพื่อซ่อนแผงด้านล่าง)")
            self.toggle_bottom_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(6, 18, 12, 0.9); color: #00FF66;
                    border: 1px solid rgba(0, 255, 102, 0.4); border-radius: 4px;
                    padding: 3px 18px; font-weight: bold; font-size: 11px;
                    font-family: 'Consolas', monospace;
                }
                QPushButton:hover {
                    background-color: #00AA55; color: #000000;
                    border-color: #00FF66;
                }
            """)
            self.main_layout.setStretch(1, 7)
            self.main_layout.setStretch(3, 3)

    def capture_js_logs(self, title):
        if "|" not in title:
            return
        prefix, msg = title.split("|", 1)
        if prefix == "LOG":
            self.debug_log.append(f"🟢 {msg}")
        elif prefix == "SUCCESS":
            self.debug_log.append(f"⭐ <font color='#4ADE80'>{msg}</font>")
        elif prefix == "ERROR":
            self.debug_log.append(f"🚨 <font color='#EF4444'>{msg}</font>")
        elif prefix == "EXPORT_3D_TRIGGER":
            self.open_export_dialog()
        elif prefix == "DATA_SYNC":
            try:
                payload = json.loads(msg)
                self.update_qt_data_panel(payload)
            except Exception as e:
                pass

    def open_export_dialog(self):
        if not hasattr(self, 'current_objects_raw') or not self.current_objects_raw:
            QMessageBox.information(self, "No Objects", "No 3D objects created yet. Please draw or create objects first.")
            return
        dlg = Export3DDialog(self, self.current_objects_raw)
        dlg.exec()

    def pick_object_color_qt(self, obj_id, cur_hex):
        color = QColorDialog.getColor(initial=QColor(cur_hex), parent=self, title="Pick Object Color")
        if color.isValid():
            hex_val = color.name()
            self.web_view.page().runJavaScript(f"modifyObjColor({obj_id}, '{hex_val}');")

    def update_qt_data_panel(self, data):
        objects = data.get("objects", [])
        images = data.get("images", [])
        self.current_objects_raw = objects

        # Update Tab 1: 3D Objects
        self.data_tabs.setTabText(0, f"🏢 Objects ({len(objects)})")
        self.obj_list_widget.clear()
        for o in objects:
            item = QListWidgetItem()
            w = QWidget()
            row = QHBoxLayout(w)
            row.setContentsMargins(6, 2, 6, 2)
            row.setSpacing(5)

            sz_val = o.get('width', o.get('size', 50))
            color_hex = o.get('colorHex', '#00E5FF')
            info_text = f"<span style='color:{color_hex}; font-size:13px;'>●</span> <b>{o['name']}</b> ({o['type'].upper()}) H:{o['height']}m Sz:{sz_val}m"
            info = QLabel(info_text)
            info.setStyleSheet("color: #E0FFE8; font-size: 11px;")
            row.addWidget(info, 1)

            oid = o['id']

            # Color Picker Button
            clr_b = QPushButton("🎨")
            clr_b.setStyleSheet(f"background: {color_hex}; color: #000; font-size: 10px; padding: 2px 6px; font-weight: bold; border: 1px solid #FFF; border-radius: 3px;")
            clr_b.setToolTip("Change object color")
            clr_b.clicked.connect(lambda checked, i=oid, cur=color_hex: self.pick_object_color_qt(i, cur))
            row.addWidget(clr_b)

            # Height +/- and direct input
            hin_b = QPushButton("+H")
            hin_b.setStyleSheet("background: #007799; color: #FFF; font-size: 10px; padding: 2px 5px; font-weight: bold;")
            hin_b.clicked.connect(lambda checked, i=oid: self.web_view.page().runJavaScript(f"modifyObjDimensions({i}, 1.0, 5);"))
            row.addWidget(hin_b)

            hout_b = QPushButton("-H")
            hout_b.setStyleSheet("background: #007799; color: #FFF; font-size: 10px; padding: 2px 5px; font-weight: bold;")
            hout_b.clicked.connect(lambda checked, i=oid: self.web_view.page().runJavaScript(f"modifyObjDimensions({i}, 1.0, -5);"))
            row.addWidget(hout_b)

            h_spin = QSpinBox()
            h_spin.setRange(1, 10000)
            h_spin.setValue(int(o.get('height', 20)))
            h_spin.setSuffix("m")
            h_spin.setToolTip("Directly edit height in meters")
            h_spin.setStyleSheet("background: #020604; color: #00FF66; border: 1px solid #00AA55; font-size: 10px; padding: 1px 2px;")
            h_spin.setFixedWidth(58)
            h_spin.editingFinished.connect(lambda s=h_spin, i=oid: self.web_view.page().runJavaScript(f"setObjHeight({i}, {s.value()});"))
            row.addWidget(h_spin)

            # Size +/-
            szin_b = QPushButton("+Sz")
            szin_b.setStyleSheet("background: #008855; color: #FFF; font-size: 10px; padding: 2px 5px; font-weight: bold;")
            szin_b.clicked.connect(lambda checked, i=oid: self.web_view.page().runJavaScript(f"modifyObjDimensions({i}, 1.15, 0);"))
            row.addWidget(szin_b)

            szout_b = QPushButton("-Sz")
            szout_b.setStyleSheet("background: #008855; color: #FFF; font-size: 10px; padding: 2px 5px; font-weight: bold;")
            szout_b.clicked.connect(lambda checked, i=oid: self.web_view.page().runJavaScript(f"modifyObjDimensions({i}, 0.85, 0);"))
            row.addWidget(szout_b)

            fly_b = QPushButton("🎯 Fly")
            fly_b.setStyleSheet("background: #00AA55; color: #000; font-size: 10px; padding: 3px 8px;")
            fly_b.clicked.connect(lambda checked, i=oid: self.web_view.page().runJavaScript(f"selectObj({i});"))
            row.addWidget(fly_b)

            del_b = QPushButton("🗑️ Del")
            del_b.setStyleSheet("background: #990000; color: #FFF; font-size: 10px; padding: 3px 8px;")
            del_b.clicked.connect(lambda checked, i=oid: self.web_view.page().runJavaScript(f"delObj({i});"))
            row.addWidget(del_b)

            item.setSizeHint(QSize(420, 36))
            self.obj_list_widget.addItem(item)
            self.obj_list_widget.setItemWidget(item, w)

        # Update Tab 2: Image Overlays
        self.data_tabs.setTabText(1, f"🖼️ Images ({len(images)})")
        self.img_list_widget.clear()
        for img in images:
            item = QListWidgetItem()
            w = QWidget()
            row = QHBoxLayout(w)
            row.setContentsMargins(6, 2, 6, 2)
            row.setSpacing(6)

            info_text = f"<b>{img['name']}</b> | {img['scale']}x | {img.get('rotation', 0)}° | 📍{img['lat']},{img['lon']}"
            info = QLabel(info_text)
            info.setStyleSheet("color: #38BDF8; font-size: 11px;")
            row.addWidget(info, 1)

            iid = img['id']
            rot_left_b = QPushButton("↶ 15°")
            rot_left_b.setStyleSheet("background: #00AA88; color: #000; font-size: 10px; padding: 3px 5px;")
            rot_left_b.clicked.connect(lambda checked, i=iid: self.web_view.page().runJavaScript(f"rotateImage({i}, -15);"))
            row.addWidget(rot_left_b)

            rot_right_b = QPushButton("↷ 15°")
            rot_right_b.setStyleSheet("background: #00AA88; color: #000; font-size: 10px; padding: 3px 5px;")
            rot_right_b.clicked.connect(lambda checked, i=iid: self.web_view.page().runJavaScript(f"rotateImage({i}, 15);"))
            row.addWidget(rot_right_b)

            zin_b = QPushButton("➕")
            zin_b.setStyleSheet("background: #007799; color: #FFF; font-size: 10px; padding: 3px 6px;")
            zin_b.clicked.connect(lambda checked, i=iid: self.web_view.page().runJavaScript(f"scaleImage({i}, 1.25);"))
            row.addWidget(zin_b)

            zout_b = QPushButton("➖")
            zout_b.setStyleSheet("background: #007799; color: #FFF; font-size: 10px; padding: 3px 6px;")
            zout_b.clicked.connect(lambda checked, i=iid: self.web_view.page().runJavaScript(f"scaleImage({i}, 0.8);"))
            row.addWidget(zout_b)

            fly_b = QPushButton("🎯 Fly")
            fly_b.setStyleSheet("background: #00AA55; color: #000; font-size: 10px; padding: 3px 8px;")
            fly_b.clicked.connect(lambda checked, i=iid: self.web_view.page().runJavaScript(f"flyToImage({i});"))
            row.addWidget(fly_b)

            del_b = QPushButton("🗑️ Del")
            del_b.setStyleSheet("background: #990000; color: #FFF; font-size: 10px; padding: 3px 8px;")
            del_b.clicked.connect(lambda checked, i=iid: self.web_view.page().runJavaScript(f"deleteImage({i});"))
            row.addWidget(del_b)

            item.setSizeHint(QSize(300, 36))
            self.img_list_widget.addItem(item)
            self.img_list_widget.setItemWidget(item, w)

        # Update Tab 3: Tactical Pins
        pins = data.get("pins", [])
        self.data_tabs.setTabText(2, f"🎯 Pins ({len(pins)})")
        self.pin_list_widget.clear()
        for p in pins:
            item = QListWidgetItem()
            w = QWidget()
            row = QHBoxLayout(w)
            row.setContentsMargins(6, 2, 6, 2)
            row.setSpacing(6)

            info_text = f"<b>{p['label']}</b> (<span style='color:#FF6B6B; font-weight:bold;'>● {p['rRed']}m</span> <span style='color:#FFAA33; font-weight:bold;'>● {p['rOrange']}m</span> <span style='color:#FFFF66; font-weight:bold;'>● {p['rYellow']}m</span>) | 📍{p['lat']},{p['lon']}"
            info = QLabel(info_text)
            info.setStyleSheet("color: #FCD34D; font-size: 11px;")
            row.addWidget(info, 1)

            pid = p['id']
            fly_b = QPushButton("🎯 Fly")
            fly_b.setStyleSheet("background: #00AA55; color: #000; font-size: 10px; padding: 3px 8px;")
            fly_b.clicked.connect(lambda checked, i=pid: self.web_view.page().runJavaScript(f"flyToPin('{i}');"))
            row.addWidget(fly_b)

            del_b = QPushButton("🗑️ Del")
            del_b.setStyleSheet("background: #990000; color: #FFF; font-size: 10px; padding: 3px 8px;")
            del_b.clicked.connect(lambda checked, i=pid: self.web_view.page().runJavaScript(f"deletePin('{i}');"))
            row.addWidget(del_b)

            item.setSizeHint(QSize(420, 36))
            self.pin_list_widget.addItem(item)
            self.pin_list_widget.setItemWidget(item, w)

# =========================================================================
# 4. Entry Point
# =========================================================================
if __name__ == "__main__":
    active_port = run_auto_port_server()
    print(f"Server started on http://127.0.0.1:{active_port}")

    os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"

    app = QApplication(sys.argv)
    window = Cesium3DIsolatedConsole(target_port=active_port)
    window.show()
    sys.exit(app.exec())
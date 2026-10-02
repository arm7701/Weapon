import sys
import os
import json
import math
import re
import html
import urllib.request
import urllib.parse
import http.server
import socketserver
import threading
import tempfile
import datetime
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
    <title>CESIUM_EXPLOSION_SIMULATOR</title>
    <script src="https://cesium.com/downloads/cesiumjs/releases/1.118/Build/Cesium/Cesium.js"></script>
    <link href="https://cesium.com/downloads/cesiumjs/releases/1.118/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { overflow: hidden; background: #0A0F1D; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Consolas', monospace; }
        #cesiumContainer { width: 100vw; height: 100vh; }

        /* ===== Unified Command & Control Header (Executive Theme) ===== */
        #unifiedTopBar {
            position: absolute; top: 0; left: 0; right: 0; z-index: 9999;
            height: 44px;
            background: rgba(15, 23, 42, 0.96);
            border-bottom: 1.5px solid #334155;
            backdrop-filter: blur(12px);
            display: flex; align-items: center; justify-content: flex-start;
            padding: 0 10px; gap: 5px; box-shadow: 0 4px 20px rgba(0,0,0,0.75);
            overflow-x: auto; overflow-y: hidden;
            scrollbar-width: thin;
            scrollbar-color: #475569 transparent;
        }
        #unifiedTopBar::-webkit-scrollbar { height: 3px; }
        #unifiedTopBar::-webkit-scrollbar-track { background: transparent; }
        #unifiedTopBar::-webkit-scrollbar-thumb { background: #475569; border-radius: 2px; }
        
        .topbar-group { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }
        .topbar-sep { width: 1px; height: 22px; background: #334155; margin: 0 4px; flex-shrink: 0; }
        
        .t-btn {
            background: #1E293B; color: #F1F5F9;
            border: 1px solid #475569;
            padding: 5px 9px; border-radius: 4px;
            font-family: inherit; font-size: 10.5px; font-weight: 600;
            cursor: pointer; transition: all 0.18s ease; white-space: nowrap; outline: none;
            display: inline-flex; align-items: center; gap: 3px;
        }
        .t-btn:hover { background: #2563EB; border-color: #3B82F6; color: #FFFFFF; box-shadow: 0 0 12px rgba(37,99,235,0.4); }
        .t-btn.active { background: #2563EB; border-color: #60A5FA; color: #FFFFFF; box-shadow: 0 0 14px rgba(37,99,235,0.6); }
        .t-btn.pin { background: #1E293B; border-color: #475569; color: #F8FAFC; }
        .t-btn.pin.active { background: #2563EB; border-color: #60A5FA; color: #FFFFFF; }
        .t-btn.wpn { background: #1E293B; border-color: #3B82F6; color: #93C5FD; }
        .t-btn.wpn:hover { background: #1D4ED8; border-color: #60A5FA; color: #FFFFFF; }
        .t-btn.blast {
            background: #DC2626; border-color: #EF4444; color: #FFFFFF;
            box-shadow: 0 0 10px rgba(220,38,38,0.4);
        }
        .t-btn.blast:hover { background: #B91C1C; box-shadow: 0 0 15px rgba(220,38,38,0.7); }
        .t-btn.video {
            background: #4F46E5; border-color: #6366F1; color: #FFFFFF;
            box-shadow: 0 0 10px rgba(99,102,241,0.35); font-weight: bold;
        }
        .t-btn.video:hover { background: #4338CA; border-color: #818CF8; box-shadow: 0 0 16px rgba(99,102,241,0.6); }
        .t-btn.video:disabled { background: #334155; border-color: #475569; color: #94A3B8; cursor: not-allowed; box-shadow: none; }
        .t-btn.loop { background: #1E293B; border-color: #475569; color: #94A3B8; }
        .t-btn.loop.active { background: #0284C7; border-color: #38BDF8; color: #FFFFFF; box-shadow: 0 0 12px rgba(56,189,248,0.6); }
        .t-btn.stop { background: #7F1D1D; border-color: #991B1B; color: #FECACA; }
        .t-btn.stop:hover { background: #991B1B; color: #FFF; }
        .t-btn.dome { background: #1E293B; border-color: #475569; color: #94A3B8; }
        .t-btn.dome:hover { background: #0284C7; border-color: #38BDF8; color: #FFF; }
        .t-btn.dome.active { background: #0284C7; border-color: #38BDF8; color: #FFFFFF; }
        .t-btn.tools { background: #1E293B; border-color: #475569; color: #E2E8F0; }
        .t-btn.tools.active { background: #2563EB; border-color: #60A5FA; color: #FFFFFF; }
        .t-btn.del { background: #7F1D1D; border-color: #991B1B; color: #FECACA; }
        .t-btn.del:hover { background: #DC2626; color: #FFF; }
        .t-btn.clear { background: #334155; border-color: #475569; color: #CBD5E1; }
        .t-btn.clear:hover { background: #475569; color: #FFF; }
        
        .t-sel {
            background: #0F172A; color: #F8FAFC;
            border: 1px solid #475569; border-radius: 4px;
            padding: 4px 6px; font-family: inherit; font-size: 10px; font-weight: bold;
            cursor: pointer; outline: none;
        }

        /* ===== Collapsible 3D Tools Drawer ===== */
        #toolsDrawer {
            position: absolute; top: 44px; left: 0; right: 0; z-index: 9997;
            height: 40px; background: rgba(15, 23, 42, 0.96);
            border-bottom: 1px solid #334155;
            backdrop-filter: blur(10px);
            display: none; align-items: center; gap: 6px; padding: 0 10px;
            animation: drawerSlide 0.2s ease;
        }
        @keyframes drawerSlide {
            from { transform: translateY(-10px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        .tb-btn {
            background: #1E293B; color: #F1F5F9;
            border: 1px solid #475569;
            padding: 5px 10px; border-radius: 4px;
            font-family: inherit; font-size: 10px; font-weight: bold;
            cursor: pointer; transition: all 0.2s; white-space: nowrap;
        }
        .tb-btn:hover { background: #2563EB; border-color: #3B82F6; color: #FFF; }
        .tb-btn.active { background: #2563EB; border-color: #60A5FA; color: #FFF; }
        .tb-sel {
            background: #0F172A; color: #F8FAFC;
            border: 1px solid #334155; border-radius: 4px;
            padding: 4px 8px; font-family: inherit; font-size: 10px;
            cursor: pointer; outline: none;
        }
        .tb-inp {
            background: #0F172A; color: #38BDF8;
            border: 1px solid #334155; border-radius: 4px;
            padding: 4px 8px; font-family: inherit; font-size: 10px;
            width: 80px; outline: none;
        }
        .tb-sep { width: 1px; height: 22px; background: #334155; margin: 0 3px; }

        /* ===== Object Data Panel (right sidebar) ===== */
        #objectPanel {
            position: absolute; top: 52px; right: 0; bottom: 0;
            width: 330px; z-index: 9998;
            background: rgba(15, 23, 42, 0.96);
            border-left: 1px solid #334155;
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
            border-bottom: 1px solid #334155;
            color: #F8FAFC; font-size: 12px; font-weight: bold; letter-spacing: 0.5px;
        }
        .pnl-cnt {
            background: #1E293B; color: #38BDF8;
            padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: bold;
        }
        #objList { flex: 1; overflow-y: auto; padding: 6px 0; }
        #objList::-webkit-scrollbar { width: 5px; }
        #objList::-webkit-scrollbar-track { background: transparent; }
        #objList::-webkit-scrollbar-thumb { background: #475569; border-radius: 3px; }

        .empty-st {
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            height: 200px; color: #64748B; gap: 10px; font-size: 12px;
        }
        .empty-st .ico { font-size: 40px; opacity: 0.5; }

        /* ===== Object Cards ===== */
        .ocard {
            margin: 4px 8px; padding: 10px 12px;
            background: #1E293B;
            border: 1px solid #334155;
            border-radius: 6px; cursor: pointer;
            transition: all 0.2s;
        }
        .ocard:hover { border-color: #3B82F6; background: #243247; }
        .ocard.sel {
            border-color: #2563EB; background: #1E3A8A;
            box-shadow: 0 0 14px rgba(37,99,235,0.3);
        }
        .ctop { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
        .cname { color: #F8FAFC; font-size: 12px; font-weight: bold; }
        .ctype { color: #38BDF8; font-size: 10px; background: rgba(56,189,248,0.1); padding: 2px 7px; border-radius: 3px; }
        .cinfo { color: #94A3B8; font-size: 10px; line-height: 1.7; }
        .cbtns { display: flex; gap: 5px; margin-top: 8px; }
        .cbtn {
            flex: 1; padding: 5px 0; text-align: center;
            background: #334155; color: #F1F5F9;
            border: 1px solid #475569; border-radius: 4px;
            font-family: inherit; font-size: 10px; cursor: pointer; transition: all 0.15s;
        }
        .cbtn:hover { background: #2563EB; border-color: #3B82F6; color: #FFF; }
        .cbtn.del { background: #7F1D1D; color: #FECACA; border-color: #991B1B; }
        .cbtn.del:hover { background: #DC2626; color: #FFF; }

        /* ===== Inline Edit Form ===== */
        .eform { display: none; margin-top: 8px; padding-top: 8px; border-top: 1px solid #334155; }
        .eform.vis { display: block; }
        .erow { display: flex; align-items: center; gap: 6px; margin-bottom: 5px; }
        .elbl { color: #94A3B8; font-size: 10px; width: 55px; text-align: right; }
        .einp {
            flex: 1; background: #0F172A; color: #38BDF8;
            border: 1px solid #334155; border-radius: 3px;
            padding: 4px 7px; font-family: inherit; font-size: 11px; outline: none;
        }
        .einp:focus { border-color: #3B82F6; box-shadow: 0 0 6px rgba(59,130,246,0.3); }
        .eacts { display: flex; gap: 5px; margin-top: 6px; }
        .eok {
            flex: 1; padding: 5px; text-align: center;
            background: #2563EB; color: #FFF; border: none; border-radius: 4px;
            font-family: inherit; font-size: 10px; font-weight: bold; cursor: pointer;
        }
        .eok:hover { background: #1D4ED8; }
        .ecc {
            flex: 1; padding: 5px; text-align: center;
            background: #334155; color: #CBD5E1; border: 1px solid #475569;
            border-radius: 4px; font-family: inherit; font-size: 10px; cursor: pointer;
        }
        .ecc:hover { background: #475569; }

        /* ===== Drawing Guide / Tactical Blast Telemetry HUD ===== */
        #drawGuide {
            position: absolute; bottom: 25px; left: 50%; transform: translateX(-50%);
            z-index: 10002; display: none;
            background: rgba(15, 23, 42, 0.96); color: #F8FAFC;
            padding: 8px 22px; border-radius: 8px;
            border: 1.5px solid #3B82F6;
            font-size: 11px; white-space: nowrap;
            backdrop-filter: blur(12px);
            box-shadow: 0 6px 25px rgba(0,0,0,0.85), 0 0 16px rgba(59,130,246,0.25);
            align-items: center; gap: 10px; pointer-events: none;
        }

        /* ===== Minimap 2D ===== */
        #minimapContainer {
            position: absolute; top: 50px; right: 10px; width: 135px; height: 135px;
            border: 2px solid #334155; border-radius: 8px; z-index: 9998;
            background: #020617; box-shadow: 0 4px 15px rgba(0,0,0,0.7); overflow: hidden;
        }

        #objectPanel { display: none !important; }

        /* ===== Floating Image Draft Control Bar ===== */
        #imageControlBar {
            position: absolute; bottom: 25px; left: 50%; transform: translateX(-50%);
            background: rgba(15, 23, 42, 0.96); border: 2px solid #3B82F6; border-radius: 8px;
            padding: 8px 16px; display: none; align-items: center; gap: 10px;
            box-shadow: 0 4px 25px rgba(0,0,0,0.85), 0 0 15px rgba(59,130,246,0.25);
            z-index: 10000; font-family: inherit; font-size: 11px; color: #F8FAFC;
        }
        .icb-title { font-weight: bold; color: #38BDF8; font-size: 12px; white-space: nowrap; margin-right: 4px; }
        .icb-group { display: flex; align-items: center; gap: 5px; white-space: nowrap; }
        .icb-group label { color: #94A3B8; font-size: 10px; }
        .icb-group input[type=range] { width: 75px; accent-color: #3B82F6; cursor: pointer; }
        .icb-btn {
            background: #1E293B; border: 1px solid #475569;
            color: #F1F5F9; padding: 4px 8px; border-radius: 4px; cursor: pointer;
            font-family: inherit; font-size: 11px; font-weight: bold; transition: all 0.15s;
        }
        .icb-btn:hover { background: #2563EB; border-color: #3B82F6; color: #FFF; }
        .icb-btn.lock { background: #1E293B; border-color: #38BDF8; color: #38BDF8; }
        .icb-btn.lock.locked { background: #D97706; border-color: #F59E0B; color: #FFF; font-weight: bold; }
        .icb-btn.del { background: #7F1D1D; border-color: #991B1B; color: #FECACA; }
        .icb-btn.del:hover { background: #DC2626; color: #FFF; }
        .icb-btn.close { background: transparent; border: none; color: #94A3B8; font-size: 14px; padding: 2px 6px; cursor: pointer; }
        .icb-btn.close:hover { color: #EF4444; }

        /* ===== Floating 3D Object Control Bar ===== */
        #objectControlBar {
            position: absolute; bottom: 25px; left: 50%; transform: translateX(-50%);
            background: rgba(15, 23, 42, 0.96); border: 2px solid #3B82F6; border-radius: 8px;
            padding: 8px 16px; display: none; align-items: center; gap: 10px;
            box-shadow: 0 4px 25px rgba(0,0,0,0.85), 0 0 15px rgba(59,130,246,0.25);
            z-index: 10000; font-family: inherit; font-size: 11px; color: #F8FAFC;
        }
        .ocb-title { font-weight: bold; color: #38BDF8; font-size: 12px; white-space: nowrap; margin-right: 4px; }
        .ocb-group { display: flex; align-items: center; gap: 5px; white-space: nowrap; }
        .ocb-inp {
            background: #0F172A; color: #F8FAFC;
            border: 1px solid #334155; border-radius: 4px;
            padding: 3px 5px; font-family: inherit; font-size: 11px; font-weight: bold;
            text-align: right; width: 55px; outline: none;
            transition: all 0.2s;
        }
        .ocb-inp:focus {
            border-color: #3B82F6;
            box-shadow: 0 0 8px rgba(59,130,246,0.5);
            background: #1E293B;
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
            background: rgba(15, 23, 42, 0.96); border: 1.5px solid #EF4444; border-radius: 8px;
            padding: 6px 14px; display: none; align-items: center; gap: 8px;
            box-shadow: 0 6px 25px rgba(0,0,0,0.85), 0 0 15px rgba(239,68,68,0.25);
            z-index: 10001; font-family: inherit; font-size: 11px; color: #F8FAFC;
            max-width: 92vw; white-space: nowrap;
        }
        .pcb-title { font-weight: bold; color: #EF4444; font-size: 12px; white-space: nowrap; margin-right: 4px; }

        /* ===== Tactical Radius Settings Box ===== */
        .tactical-cfg-box {
            position: absolute; top: 45px; left: 0;
            background: rgba(15, 23, 42, 0.98); border: 2px solid #334155; border-radius: 8px;
            padding: 12px 16px; box-shadow: 0 8px 30px rgba(0,0,0,0.85);
            z-index: 10001; font-family: inherit; font-size: 11px; color: #F8FAFC;
            width: 420px;
        }
        .tcb-header {
            display: flex; justify-content: space-between; align-items: center;
            border-bottom: 1px solid #334155; padding-bottom: 6px; margin-bottom: 10px;
        }
        .tcb-title {
            font-weight: bold; color: #F8FAFC; font-size: 12px; letter-spacing: 0.5px;
        }
        .tcb-close-btn {
            background: transparent; border: none; color: #94A3B8; font-size: 14px;
            cursor: pointer; padding: 0 4px; transition: color 0.2s;
        }
        .tcb-close-btn:hover { color: #EF4444; }

        /* Weapon selection cards */
        .wpn-btn {
            flex: 1; padding: 8px 10px; background: #1E293B;
            border: 2px solid #334155; border-radius: 6px;
            color: #F8FAFC; font-family: inherit; text-align: left;
            cursor: pointer; transition: all 0.2s;
        }
        .wpn-btn:hover {
            background: #243247; border-color: #3B82F6;
            box-shadow: 0 0 10px rgba(59,130,246,0.3);
        }
        .wpn-btn.active {
            background: #1E293B; border-color: #3B82F6;
            box-shadow: 0 0 12px rgba(59,130,246,0.5);
        }
        .wpn-btn.active .wpn-title { color: #38BDF8; }

        /* Mode selection buttons */
        .mode-btn {
            flex: 1; padding: 4px 6px; background: #1E293B;
            border: 1px solid #334155; border-radius: 4px;
            color: #94A3B8; font-family: inherit; font-size: 10px;
            cursor: pointer; transition: all 0.2s; text-align: center;
        }
        .mode-btn:hover { background: #243247; border-color: #3B82F6; color: #F8FAFC; }
        .mode-btn.active {
            background: #2563EB; color: #FFF; font-weight: bold;
            border-color: #3B82F6; box-shadow: 0 0 8px rgba(37,99,235,0.4);
        }

        /* 3-Zone preview card */
        .tcb-preview-card {
            background: #0F172A; border: 1px solid #334155;
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
            background: #1E293B; color: #94A3B8; padding: 4px 6px;
            text-align: left; border: 1px solid #334155;
        }
        .tcb-table td {
            padding: 3px 6px; border: 1px solid #334155;
            color: #E2E8F0; background: #0F172A;
        }
        .tcb-table tr:nth-child(even) td { background: #162032; }

        .tcb-inp {
            background: #0F172A; border: 1px solid #475569;
            color: #FFF; padding: 3px 8px; border-radius: 4px; font-family: inherit;
            font-size: 11px;
        }
        .tcb-inp:focus { border-color: #3B82F6; outline: none; box-shadow: 0 0 6px rgba(59,130,246,0.4); }

        /* ===== Video Recording HUD & Animation ===== */
        @keyframes recBlink {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.3; transform: scale(0.85); }
        }
        .rec-blink {
            animation: recBlink 1.2s infinite ease-in-out;
        }
        #videoRecordingHUD {
            position: absolute; top: 54px; left: 50%; transform: translateX(-50%);
            background: rgba(15, 23, 42, 0.94); border: 1.5px solid #EF4444; border-radius: 8px;
            padding: 7px 18px; z-index: 10005; box-shadow: 0 8px 30px rgba(0,0,0,0.85);
            display: none; align-items: center; gap: 14px;
            font-family: inherit; color: #F8FAFC;
            backdrop-filter: blur(10px);
        }

        /* Cesium overrides */
        .cesium-viewer-bottom { display: none !important; }
    </style>
</head>
<body>
    <div id="cesiumContainer"></div>
    <!-- 🕹️ Unified Military Command & Control Header Bar (Compact & Responsive) -->
    <div id="unifiedTopBar">
        <!-- Section 1: Tactical Target Mode & Weapon Config -->
        <div class="topbar-group">
            <button id="pinModeBtn" class="t-btn pin active" onclick="togglePinMode()">🎯 PIN: ON</button>
            <button id="radiusCfgBtn" class="t-btn wpn" onclick="toggleRadiusConfig()">⚙️ MK-82 (9m/15.2m/1219m)</button>
        </div>

        <div class="topbar-sep"></div>

        <!-- Section 2: Blast Simulation & Replay Engine -->
        <div class="topbar-group">
            <button id="animToggleBtn" class="t-btn blast" onclick="toggleAnimMode()" style="display:none;">💥 ANIM</button>
            <button id="replayBlastBtn" class="t-btn blast" onclick="replayActivePinAnim()" title="เล่นอนิเมชั่นระเบิดซ้ำ (Replay Blast Animation)">💥 REPLAY</button>
            <button id="loopToggleBtn" class="t-btn loop" onclick="toggleLoopMode()" title="เปิด/ปิดการเล่นระเบิดวนซ้ำต่อเนื่อง">🔁 LOOP: OFF</button>
            <button id="stopAnimBtn" class="t-btn stop" onclick="stopAllAnimations()" title="หยุดอนิเมชั่นและแสดงโซนปกติทันที">⏹️ STOP</button>
            <select id="animSpeedSel" class="t-sel" onchange="setAnimSpeed(this.value)" title="Blast Animation Speed">
                <option value="1">⚡ 1x</option>
                <option value="0.5">⏱️ 0.5x</option>
                <option value="2">⏩ 2x</option>
            </select>
            <button id="domeToggleBtn" class="t-btn dome active" onclick="toggleDomeMode()" title="เปิด/ปิดการแสดงโดมครอบ 3 มิติ (Toggle 3D Covering Domes)">🌐 DOME: ON</button>
        </div>

        <div class="topbar-sep"></div>

        <!-- Section 3: 3D Tools Drawer & Map Cleaning -->
        <div class="topbar-group">
            <button id="toolsToggleBtn" class="t-btn tools" onclick="toggleToolsDrawer()">🔧 3D TOOLS ▾</button>
            <button class="t-btn del" onclick="deleteLastPin()" title="Delete last tactical pin">🗑️ DEL</button>
            <button class="t-btn clear" onclick="clearAllPins()" title="Clear all pins">❌ CLEAR</button>
        </div>

        <div class="topbar-sep"></div>

        <!-- Section 4: 360° Video Orbit Export Engine -->
        <div class="topbar-group">
            <select id="exportOrbitMode" class="t-sel" style="background:#1E293B; border-color:#0284C7; color:#38BDF8; font-size:11px; font-weight:bold; padding:3px 7px; border-radius:4px;" title="เลือกโหมดกล้องเมื่อบันทึกวิดีโอ 360°">
                <option value="cluster" selected>🎯 แสดงพร้อมกัน (หมุนจุดกลาง)</option>
                <option value="sequence">🔄 บินดูทีละจุด (ตามลำดับ)</option>
            </select>
            <button id="exportVideoBtn" class="t-btn video" onclick="triggerVideoExportDialog()" title="บันทึกวิดีโอ 360° การจำลองรัศมีระเบิดและพื้นที่เป้าหมายเป็นไฟล์ MP4">🎥 EXPORT MP4</button>
        </div>
    </div>

    <!-- 🎥 Video Recording Overlay HUD -->
    <div id="videoRecordingHUD">
        <div style="display:flex; align-items:center; gap:8px;">
            <span class="rec-blink" style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#EF4444; box-shadow:0 0 10px #EF4444;"></span>
            <span style="font-weight:bold; font-size:11px; letter-spacing:0.5px; color:#F8FAFC;">REC 360° BLAST ORBIT</span>
        </div>
        <div id="recProgressText" style="font-size:11px; font-weight:bold; color:#38BDF8; font-variant-numeric:tabular-nums;">00:00 / 00:20</div>
        <div style="width:110px; height:5px; background:#334155; border-radius:3px; overflow:hidden;">
            <div id="recProgressBar" style="width:0%; height:100%; background:#EF4444; transition:width 0.1s linear;"></div>
        </div>
        <button id="instantShowAllBtn" class="t-btn" onclick="instantShowAllRadiusAndCenter()" style="padding:2px 8px; font-size:10px; background:#0284C7; border-color:#38BDF8; color:#FFF; font-weight:bold; display:none;" title="แสดงจุดรัศมีระเบิดทั้งหมดทันที และสลับไปหมุนรอบจุดกลาง">⏩ แสดงจุดทั้งหมดทันที</button>
        <button class="t-btn stop" onclick="cancelVideoRecording()" style="padding:2px 8px; font-size:10px;" title="Cancel recording and restore camera">✖ CANCEL</button>
    </div>

    <!-- 📋 Video Recording Mission Info Card (Top-Left Tactical HUD) -->
    <div id="videoMissionInfoCard" style="display:none; position:absolute; top:54px; left:20px; z-index:99999; background:rgba(15,23,42,0.88); border:1px solid #38BDF8; border-left:5px solid #38BDF8; border-radius:8px; padding:10px 14px; color:#F8FAFC; font-family:'Segoe UI', Tahoma, sans-serif; min-width:320px; max-width:440px; box-shadow:0 10px 25px rgba(0,0,0,0.5); backdrop-filter:blur(6px); pointer-events:none;">
    </div>

    <!-- 🛠️ Collapsible 3D Tools Drawer (Expands below header only when requested) -->
    <div id="toolsDrawer">
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
        <label style="color:#94A3B8; font-size:10px; font-weight:bold;">🎨 COLOR:</label>
        <input type="color" id="toolbarColorPicker" value="#EDE8DE" style="width:20px; height:20px; border:1px solid #475569; border-radius:3px; padding:0; background:#0F172A; cursor:pointer;" title="Choose color for new shapes" onchange="setGlobalDrawColor(this.value)">
        <div class="tb-sep"></div>
        <button class="tb-btn" onclick="reportStatus('EXPORT_3D_TRIGGER', '1')" style="background: #1E293B; border-color: #38BDF8; color: #38BDF8;">📤 EXPORT 3D</button>
    </div>

    <!-- ⚙️ Tactical Weapon Preset Box (Positioned cleanly under Weapon Button) -->
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
                    <div style="font-size: 9px; opacity: 0.85; color: #94A3B8;">500 lb GP Bomb</div>
                </button>
                <button id="wpnBtnMK84" class="wpn-btn" onclick="selectWeapon('MK-84')">
                    <div class="wpn-title" style="font-size: 12px; font-weight: bold;">💣 MK-84</div>
                    <div style="font-size: 9px; opacity: 0.85; color: #94A3B8;">2,000 lb GP Bomb</div>
                </button>
            </div>
        </div>

        <!-- Effect Mode Selector -->
        <div style="margin-bottom: 8px;">
            <div style="color: #94A3B8; font-weight: bold; margin-bottom: 4px; font-size: 10px;">🎯 EFFECT VIEW MODE (รูปแบบโซน 3 สี):</div>
            <div style="display: flex; gap: 4px;">
                <button id="modeBtnFull" class="mode-btn active" onclick="selectEffectMode('full')">Full Effect (Pen/Blast/Frag)</button>
                <button id="modeBtnFrag" class="mode-btn" onclick="selectEffectMode('frag')">Frag (Front/Rear/Side)</button>
                <button id="modeBtnPen" class="mode-btn" onclick="selectEffectMode('penetration')">Crater & Upheaval</button>
            </div>
        </div>

        <!-- Active 3-Zone Display Preview -->
        <div class="tcb-preview-card">
            <div style="font-weight: bold; color: #FFF; margin-bottom: 5px; display: flex; justify-content: space-between; align-items: center;">
                <span id="cfgActiveName" style="color: #38BDF8;">💣 MK-82 ACTIVE PRESET</span>
                <span id="cfgActiveModeLabel" style="color: #94A3B8; font-size: 10px; font-weight: normal;">Full Effect</span>
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
            <div style="font-weight: bold; color: #F8FAFC; font-size: 10px; margin-bottom: 3px; display: flex; align-items: center; justify-content: space-between;">
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
            <button class="t-btn" onclick="applyPresetAndClose()" style="flex: 1; padding: 4px 8px; background: #2563EB; color: #FFFFFF; border-color: #3B82F6; font-size: 10px; font-weight: bold;">✓ APPLY & CLOSE</button>
        </div>
    </div>
    <div id="minimapContainer"></div>

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
        <span id="ocbDamageBadge" style="display:none; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:bold;"></span>
        <button id="ocbRepairBtn" class="icb-btn" onclick="if(selectedObjectId!==null) repairSingleBuilding(selectedObjectId)" style="display:none; background:#0284C7; border-color:#38BDF8; color:#FFF;" title="Repair this building to 100% (ซ่อมแซมอาคารนี้)">🔨 REPAIR</button>
        
        <div class="ocb-group">
            <label>📏 Height:</label>
            <button class="icb-btn" onclick="modifyActiveObject(1.0, -5)" title="ลดความสูง 5m">➖5m</button>
            <div style="display:inline-flex; align-items:center; gap:2px;">
                <input type="number" id="ocbHeightInput" class="ocb-inp" min="1" max="10000" step="1" value="20"
                       title="กรอกตัวเลขความสูงโดยตรง (กด Enter เพื่อปรับ)"
                       onchange="setActiveObjectHeight(this.value)"
                       onkeydown="if(event.key==='Enter'){ setActiveObjectHeight(this.value); this.blur(); }">
                <span style="color:#38BDF8; font-size:11px; font-weight:bold;">m</span>
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

        <button class="icb-btn" onclick="flyToActiveObject()" style="background:#2563EB; color:#FFF;">🎯 FLY</button>
        <button class="icb-btn del" onclick="deleteActiveObject()">🗑️ DELETE</button>
        <button class="icb-btn close" onclick="closeObjectControlBar()">✖</button>
    </div>

    <!-- 🎯 Floating Tactical Pin Control Bar -->
    <div id="pinControlBar">
        <div class="pcb-title"><span id="pcbName">🎯 PIN</span></div>
        <span id="pcbInfo" style="color: #FDE047; font-size: 11px;"></span>
        <button class="icb-btn" onclick="replayActivePinAnim()" style="background: rgba(220, 80, 0, 0.85); border: 1px solid #FF8800; color: #FFF; font-weight: bold; margin-right: 2px;">💥 REPLAY</button>
        <button id="pcbLoopBtn" class="icb-btn" onclick="toggleLoopMode()" style="background: rgba(20, 30, 45, 0.85); border: 1px solid #1E3A8A; color: #38BDF8; font-weight: bold; margin-right: 2px;">🔁 LOOP</button>
        <button class="icb-btn" onclick="stopAllAnimations()" style="background: rgba(100, 20, 20, 0.85); border: 1px solid #FF4444; color: #FFAAAA; font-weight: bold; margin-right: 2px;">⏹️ STOP</button>
        <button class="icb-btn" onclick="flyToActivePin()" style="background:#2563EB; color:#FFF;">🎯 FLY</button>
        <button class="icb-btn del" onclick="deleteActivePin()">🗑️ DEL PIN</button>
        <button class="icb-btn close" onclick="closePinControlBar()">✖</button>
    </div>

    <script>
        // ===== Global Error Protection & Safeguards (JS -> Python Crash Reporting) =====
        window.onerror = function(message, source, lineno, colno, error) {
            var errText = (message || 'Unknown error') + (lineno ? ' (' + lineno + ':' + (colno || 0) + ')' : '');
            reportStatus('ERROR', 'JS Exception: ' + errText);
            return false;
        };
        window.addEventListener('unhandledrejection', function(event) {
            var reason = event.reason ? (event.reason.message || event.reason) : 'Unknown Promise Rejection';
            reportStatus('ERROR', 'JS Unhandled Rejection: ' + reason);
        });

        // ===== Status Reporting (JS → Python via document.title with Anti-Suppression Sequence) =====
        let _statusSeq = 0;
        function reportStatus(type, msg) {
            try {
                _statusSeq = (_statusSeq + 1) % 1000000;
                var safeMsg = (msg !== undefined && msg !== null) ? (typeof msg === 'string' ? msg : JSON.stringify(msg)) : '';
                document.title = type + '|' + _statusSeq + '|' + safeMsg;
            } catch(e) {}
        }
        reportStatus('LOG', 'Initializing Interactive Edit Mode Engine...');

        // ===== Shape Configuration (Architectural Aesthetics matching Cesium OSM Buildings) =====
        const SCFG = {
            box:      { icon: '📦', label: 'BOX',      clr: [0.93, 0.91, 0.87], out: [0.24, 0.24, 0.26] },
            cylinder: { icon: '🛢️', label: 'CYLINDER', clr: [0.88, 0.90, 0.92], out: [0.22, 0.24, 0.26] },
            cone:     { icon: '📐', label: 'CONE',      clr: [0.92, 0.89, 0.84], out: [0.25, 0.22, 0.20] },
            sphere:   { icon: '⚽', label: 'SPHERE',    clr: [0.88, 0.88, 0.92], out: [0.22, 0.22, 0.26] },
            polygon:  { icon: '🛑', label: 'POLYGON',   clr: [0.93, 0.91, 0.87], out: [0.24, 0.24, 0.26] }
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

        let currentDrawColor = '#EDE8DE';

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
                homeButton: false, sceneModePicker: false, skyBox: false, skyAtmosphere: false,
                contextOptions: {
                    webgl: {
                        preserveDrawingBuffer: true
                    }
                }
            });

            viewer.clock.shouldAnimate = true; // Crucial for Cesium.ParticleSystem to emit and update
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

            // 🏢 OSM 3D Buildings (built-in — ระบบอาคาร 3 มิติพร้อมรองรับ Damage Shader)
            Cesium.createOsmBuildingsAsync().then(function(t) {
                viewer.scene.primitives.add(t);
                window.osmBuildingsTileset = t;
                reportStatus('LOG', '3D Buildings loaded.');
                if (typeof initOsmDamageShader === 'function') initOsmDamageShader();
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
                if (!screenPos || !viewer || !viewer.camera) return null;
                var ray = viewer.camera.getPickRay(screenPos);
                if (!ray) return null;
                var c = null;
                try {
                    c = viewer.scene.globe.pick(ray, viewer.scene);
                } catch(e) {}
                if (!Cesium.defined(c)) {
                    try { c = viewer.scene.pickPosition(screenPos); } catch(e) {}
                }
                if (!Cesium.defined(c)) {
                    try { c = viewer.camera.pickEllipsoid(screenPos, viewer.scene.globe.ellipsoid); } catch(e) {}
                }
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
            let pinMode = true;
            window.pinRegistry = [];
            var pinRegistry = window.pinRegistry;

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
                    btn.textContent = '🎯 PIN: ON';
                    btn.style.background = '#2563EB';
                    btn.style.borderColor = '#60A5FA';
                    btn.style.color = '#FFFFFF';
                    btn.style.boxShadow = '0 0 12px rgba(37, 99, 235, 0.5)';
                    btn.classList.add('active');
                    if (editMode) toggleEditMode(false);
                    reportStatus('LOG', 'Pin Mode: ON (คลิกบนแผนที่เพื่อวางจุดรัศมี ' + tacticalRadiusConfig.label + ' 🔴' + formatR(tacticalRadiusConfig.rRed) + ' 🟠' + formatR(tacticalRadiusConfig.rOrange) + ' 🟡' + formatR(tacticalRadiusConfig.rYellow) + ')');
                } else {
                    btn.textContent = '🎯 PIN: OFF';
                    btn.style.background = '#1E293B';
                    btn.style.borderColor = '#475569';
                    btn.style.color = '#94A3B8';
                    btn.style.boxShadow = 'none';
                    btn.classList.remove('active');
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

            window.toggleToolsDrawer = function() {
                var drawer = document.getElementById('toolsDrawer');
                var btn = document.getElementById('toolsToggleBtn');
                if (drawer) {
                    var isHidden = (drawer.style.display === 'none' || !drawer.style.display);
                    drawer.style.display = isHidden ? 'flex' : 'none';
                    if (btn) {
                        if (isHidden) {
                            btn.classList.add('active');
                            btn.textContent = '🔧 3D TOOLS ▴';
                        } else {
                            btn.classList.remove('active');
                            btn.textContent = '🔧 3D TOOLS ▾';
                        }
                    }
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
                    btn.textContent = '⚙️ ' + currentWeaponKey + ' (' + formatR(modeData.rRed) + '/' + formatR(modeData.rOrange) + '/' + formatR(modeData.rYellow) + ')';
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
                        html += '<tr><td><b>' + row.type + '</b></td><td>' + row.param + '</td><td><span style="color:#FDE047;">' + row.raw + '</span></td><td><span style="color:#38BDF8; font-weight:bold;">' + row.meters + '</span></td></tr>';
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

                ctx.fillStyle = 'rgba(15, 23, 42, 0.96)';
                ctx.shadowColor = 'rgba(0, 0, 0, 0.7)';
                ctx.shadowBlur = 10 * dpr;
                ctx.shadowOffsetY = 2 * dpr;
                ctx.fill();

                ctx.shadowColor = 'transparent';
                ctx.lineWidth = 1.5 * dpr;
                ctx.strokeStyle = '#38BDF8';
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

            // =================================================================
            // EXPLOSION ANIMATION ENGINE — จำลองการขยายตัวของคลื่นระเบิดและรัศมี 3D สมจริง
            // รองรับ: ลูกไฟอันตรายถึงชีวิต + เสาควันเห็ดลอยตัว + คลื่นลมกระแทก + วนลูป/หยุด
            // =================================================================
            var animEnabled = true;
            var animLoop = false;
            var animSpeed = 1.0;
            var animLoopTimer = null;
            var domeEnabled = true;
            var currentAnimController = null;
            window.currentAnimController = currentAnimController;

            window.toggleDomeMode = function() {
                domeEnabled = !domeEnabled;
                var btn = document.getElementById('domeToggleBtn');
                if (btn) {
                    if (domeEnabled) {
                        btn.classList.add('active');
                        btn.innerText = '🌐 DOME: ON';
                    } else {
                        btn.classList.remove('active');
                        btn.innerText = '🌐 DOME: OFF';
                    }
                }
                for (var i = 0; i < pinRegistry.length; i++) {
                    var p = pinRegistry[i];
                    if (p && p.entities) {
                        for (var j = 0; j < p.entities.length; j++) {
                            if (p.entities[j]._isDome) {
                                p.entities[j].show = domeEnabled;
                            }
                        }
                    }
                }
                reportStatus('LOG', '3D Covering Domes: ' + (domeEnabled ? 'ON' : 'OFF'));
            };

            window.toggleAnimMode = function() {
                animEnabled = !animEnabled;
                var btn = document.getElementById('animToggleBtn');
                if (btn) {
                    if (animEnabled) {
                        btn.textContent = '💥 ANIM: ON';
                        btn.style.background = 'rgba(220, 80, 0, 0.85)';
                        btn.style.borderColor = '#FF8800';
                        btn.style.boxShadow = '0 0 12px rgba(255, 136, 0, 0.7)';
                    } else {
                        btn.textContent = '💥 ANIM: OFF';
                        btn.style.background = 'rgba(70, 35, 15, 0.8)';
                        btn.style.borderColor = '#774422';
                        btn.style.boxShadow = 'none';
                        if (animLoop) toggleLoopMode();
                    }
                }
                reportStatus('LOG', 'Explosion Animation: ' + (animEnabled ? 'ON' : 'OFF'));
            };

            window.toggleLoopMode = function() {
                animLoop = !animLoop;
                updateLoopButtons();
                if (animLoop) {
                    reportStatus('LOG', '🔁 Loop Mode: ON (จะเล่นระเบิดวนซ้ำต่อเนื่องอัตโนมัติ)');
                    if (pinRegistry && pinRegistry.length > 1) {
                        playMultiPinBlastAnimation(pinRegistry, true);
                    } else if (pinRegistry && pinRegistry.length === 1) {
                        replayActivePinAnim();
                    }
                } else {
                    if (animLoopTimer) {
                        clearTimeout(animLoopTimer);
                        animLoopTimer = null;
                    }
                    if (currentAnimController && typeof currentAnimController.stop === 'function') {
                        currentAnimController.stop();
                        currentAnimController = null;
                    }
                    if (pinRegistry) {
                        for (var i = 0; i < pinRegistry.length; i++) {
                            var p = pinRegistry[i];
                            if (p && p.entities) {
                                for (var j = 0; j < p.entities.length; j++) {
                                    if (p.entities[j]) {
                                        p.entities[j].show = p.entities[j]._isDome ? !!domeEnabled : true;
                                    }
                                }
                            }
                        }
                    }
                    reportStatus('LOG', '🔁 Loop Mode: OFF (ปิดการเล่นวนซ้ำแล้ว)');
                }
            };

            function updateLoopButtons() {
                var btnTop = document.getElementById('loopToggleBtn');
                var btnPcb = document.getElementById('pcbLoopBtn');
                var list = [btnTop, btnPcb];
                for (var i = 0; i < list.length; i++) {
                    var b = list[i];
                    if (!b) continue;
                    if (animLoop) {
                        b.textContent = '🔁 LOOP: ON';
                        b.style.background = '#0284C7';
                        b.style.borderColor = '#38BDF8';
                        b.style.boxShadow = '0 0 12px rgba(56, 189, 248, 0.8)';
                        b.classList.add('active');
                    } else {
                        b.textContent = '🔁 LOOP: OFF';
                        b.style.background = 'rgba(20, 30, 45, 0.85)';
                        b.style.borderColor = '#1E3A8A';
                        b.style.boxShadow = 'none';
                        b.classList.remove('active');
                    }
                }
            }

            window.stopAllAnimations = function() {
                if (animLoop) {
                    animLoop = false;
                    updateLoopButtons();
                }
                if (animLoopTimer) {
                    clearTimeout(animLoopTimer);
                    animLoopTimer = null;
                }
                if (currentAnimController && typeof currentAnimController.stop === 'function') {
                    currentAnimController.stop();
                    currentAnimController = null;
                }
                // แสดงองค์ประกอบหมุดทั้งหมดให้ครบถ้วนทันที (รวมโดม 3 มิติตามสถานะ domeEnabled)
                for (var i = 0; i < pinRegistry.length; i++) {
                    var p = pinRegistry[i];
                    if (p && p.entities) {
                        for (var j = 0; j < p.entities.length; j++) {
                            if (p.entities[j]._isDome) {
                                p.entities[j].show = domeEnabled;
                            } else {
                                p.entities[j].show = true;
                            }
                        }
                    }
                }
                var guideEl = document.getElementById('drawGuide');
                if (guideEl && !isDrawing) guideEl.style.display = 'none';
                reportStatus('LOG', '⏹️ Stopped explosion animation. Restored standard view.');
            };

            window.setAnimSpeed = function(val) {
                animSpeed = parseFloat(val) || 1.0;
                reportStatus('LOG', 'Animation Speed set to: ' + animSpeed + 'x');
            };

            function playExplosionSound() {
                try {
                    var AudioCtx = window.AudioContext || window.webkitAudioContext;
                    if (!AudioCtx) return;
                    var ctx = window._sharedAudioCtx || (window._sharedAudioCtx = new AudioCtx());
                    if (ctx.state === 'suspended') {
                        ctx.resume().catch(function(){});
                    }

                    var rate = ctx.sampleRate;
                    var spd = animSpeed || 1.0;
                    var dur = 2.4 / spd;

                    // 1. Heavy sub-bass concussion drop (แรงอัดกระแทกเบสหนัก)
                    var osc = ctx.createOscillator();
                    var oscGain = ctx.createGain();
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(110, ctx.currentTime);
                    osc.frequency.exponentialRampToValueAtTime(24, ctx.currentTime + (0.4 / spd));
                    oscGain.gain.setValueAtTime(0.85, ctx.currentTime);
                    oscGain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + (0.5 / spd));
                    osc.connect(oscGain);
                    oscGain.connect(ctx.destination);
                    osc.start(ctx.currentTime);
                    osc.stop(ctx.currentTime + (0.55 / spd));

                    // 2. Initial supersonic blast crack (เสียงแตกหักระเบิดเฉียบพลัน)
                    var crackSize = Math.floor(rate * 0.12);
                    var crackBuf = ctx.createBuffer(1, crackSize, rate);
                    var cd = crackBuf.getChannelData(0);
                    for (var i = 0; i < crackSize; i++) {
                        cd[i] = (Math.random() * 2 - 1) * Math.exp(-i / (rate * 0.02));
                    }
                    var crack = ctx.createBufferSource();
                    crack.buffer = crackBuf;
                    var crackFilter = ctx.createBiquadFilter();
                    crackFilter.type = 'highpass';
                    crackFilter.frequency.setValueAtTime(350, ctx.currentTime);
                    var crackGain = ctx.createGain();
                    crackGain.gain.setValueAtTime(0.7, ctx.currentTime);
                    crackGain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + (0.12 / spd));
                    crack.connect(crackFilter);
                    crackFilter.connect(crackGain);
                    crackGain.connect(ctx.destination);
                    crack.start(ctx.currentTime);

                    // 3. Deep rolling atmospheric thunder & blast wind rumble (เสียงลมพายุและแรงสะท้อนก้อง)
                    var rumbleSize = Math.floor(rate * Math.min(dur, 2.5));
                    var rumbleBuf = ctx.createBuffer(1, rumbleSize, rate);
                    var rd = rumbleBuf.getChannelData(0);
                    var lastOut = 0.0;
                    for (var j = 0; j < rumbleSize; j++) {
                        var white = Math.random() * 2 - 1;
                        rd[j] = (lastOut + (0.02 * white)) / 1.02;
                        lastOut = rd[j];
                        rd[j] *= 3.5 * Math.exp(-j / (rate * 0.85));
                    }
                    var rumble = ctx.createBufferSource();
                    rumble.buffer = rumbleBuf;
                    var rumbleFilter = ctx.createBiquadFilter();
                    rumbleFilter.type = 'lowpass';
                    rumbleFilter.frequency.setValueAtTime(600, ctx.currentTime);
                    rumbleFilter.frequency.exponentialRampToValueAtTime(28, ctx.currentTime + dur);
                    var rumbleGain = ctx.createGain();
                    rumbleGain.gain.setValueAtTime(0.9, ctx.currentTime);
                    rumbleGain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dur);
                    rumble.connect(rumbleFilter);
                    rumbleFilter.connect(rumbleGain);
                    rumbleGain.connect(ctx.destination);
                    rumble.start(ctx.currentTime);
                    rumble.stop(ctx.currentTime + dur);
                } catch(e) {}
            }

            // =================================================================
            // PROCEDURAL PARTICLE TEXTURES (Dynamic Canvas Sprites - 100% Offline)
            // =================================================================
            function getFireParticleTexture() {
                if (window._cachedFireTex) return window._cachedFireTex;
                var c = document.createElement('canvas');
                c.width = 64; c.height = 64;
                var ctx = c.getContext('2d');
                var g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
                g.addColorStop(0.0, 'rgba(255, 255, 255, 1.0)'); // Blinding white core
                g.addColorStop(0.18, 'rgba(255, 235, 110, 0.98)');
                g.addColorStop(0.38, 'rgba(255, 130, 15, 0.90)'); // Incandescent orange
                g.addColorStop(0.65, 'rgba(225, 35, 5, 0.75)');   // Fiery red
                g.addColorStop(0.85, 'rgba(110, 15, 5, 0.35)');   // Smoldering soot edge
                g.addColorStop(1.0, 'rgba(0, 0, 0, 0.0)');
                ctx.fillStyle = g;
                ctx.fillRect(0, 0, 64, 64);
                window._cachedFireTex = c.toDataURL();
                return window._cachedFireTex;
            }

            function getSmokeParticleTexture() {
                if (window._cachedSmokeTex) return window._cachedSmokeTex;
                var c = document.createElement('canvas');
                c.width = 64; c.height = 64;
                var ctx = c.getContext('2d');
                var lobes = [
                    { x: 32, y: 32, r: 24, a: 0.72 },
                    { x: 23, y: 25, r: 17, a: 0.62 },
                    { x: 41, y: 25, r: 17, a: 0.62 },
                    { x: 25, y: 39, r: 16, a: 0.60 },
                    { x: 39, y: 39, r: 16, a: 0.60 }
                ];
                for (var i = 0; i < lobes.length; i++) {
                    var lb = lobes[i];
                    var g = ctx.createRadialGradient(lb.x, lb.y, 0, lb.x, lb.y, lb.r);
                    g.addColorStop(0.0, 'rgba(42, 36, 32, ' + lb.a + ')');
                    g.addColorStop(0.6, 'rgba(32, 28, 25, ' + (lb.a * 0.75) + ')');
                    g.addColorStop(1.0, 'rgba(20, 18, 16, 0.0)');
                    ctx.fillStyle = g;
                    ctx.beginPath();
                    ctx.arc(lb.x, lb.y, lb.r, 0, Math.PI * 2);
                    ctx.fill();
                }
                window._cachedSmokeTex = c.toDataURL();
                return window._cachedSmokeTex;
            }

            function getSparkParticleTexture() {
                if (window._cachedSparkTex) return window._cachedSparkTex;
                var c = document.createElement('canvas');
                c.width = 32; c.height = 32;
                var ctx = c.getContext('2d');
                var g = ctx.createRadialGradient(16, 16, 0, 16, 16, 16);
                g.addColorStop(0.0, 'rgba(255, 255, 220, 1.0)');
                g.addColorStop(0.25, 'rgba(255, 180, 50, 0.95)');
                g.addColorStop(0.65, 'rgba(255, 60, 10, 0.50)');
                g.addColorStop(1.0, 'rgba(255, 0, 0, 0.0)');
                ctx.fillStyle = g;
                ctx.fillRect(0, 0, 32, 32);
                window._cachedSparkTex = c.toDataURL();
                return window._cachedSparkTex;
            }

            function getDustParticleTexture() {
                if (window._cachedDustTex) return window._cachedDustTex;
                var c = document.createElement('canvas');
                c.width = 64; c.height = 64;
                var ctx = c.getContext('2d');
                var g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
                g.addColorStop(0.0, 'rgba(180, 160, 135, 0.65)');
                g.addColorStop(0.5, 'rgba(150, 130, 105, 0.40)');
                g.addColorStop(0.85, 'rgba(120, 105, 85, 0.15)');
                g.addColorStop(1.0, 'rgba(100, 85, 70, 0.0)');
                ctx.fillStyle = g;
                ctx.fillRect(0, 0, 64, 64);
                window._cachedDustTex = c.toDataURL();
                return window._cachedDustTex;
            }

            // =================================================================
            // 3D BUILDING DAMAGE SIMULATION ENGINE (DISABLED)
            // ยกเลิกเงื่อนไขอนิเมชันความเสียหายของตึกอาคารในรัศมีระเบิดตามความต้องการของผู้ใช้
            // =================================================================
            var buildingDamageEnabled = false;
            var osmDamageShader = null;
            var buildingRuinParticles = [];

            function playBuildingCollapseSound() {
                // Sound disabled with building damage
                return;
            }

            var _scratchCart = new Cesium.Cartesian3();
            var _lastCamViewMatrix = new Cesium.Matrix4();
            var _pinPosEC = [
                new Cesium.Cartesian3(),
                new Cesium.Cartesian3(),
                new Cesium.Cartesian3(),
                new Cesium.Cartesian3(),
                new Cesium.Cartesian3(),
                new Cesium.Cartesian3()
            ];

            function initOsmDamageShader() {
                if (window.osmBuildingsTileset) {
                    window.osmBuildingsTileset.customShader = null;
                }
                osmDamageShader = null;
            }

            function updateOsmShaderUniforms(animatingPinId, animatedRadius) {
                // Building damage shader disabled
                return;
            }

            function createBuildingRuinSmoke(lat, lon, alt, isDestroyed) {
                // Limit maximum active particle systems to prevent WebGL memory exhaustion / crash
                if (buildingRuinParticles.length >= 8) {
                    var oldPS = buildingRuinParticles.shift();
                    try { viewer.scene.primitives.remove(oldPS); } catch(e) {}
                }

                var pos = Cesium.Cartesian3.fromDegrees(lon, lat, alt || 0);
                var posMatrix = Cesium.Transforms.eastNorthUpToFixedFrame(pos);
                var upVector = Cesium.Ellipsoid.WGS84.geodeticSurfaceNormal(pos);
                var scratchVec = new Cesium.Cartesian3();

                // 1. Smoldering Black/Dark Smoke
                var smokePS = new Cesium.ParticleSystem({
                    image: getSmokeParticleTexture(),
                    startColor: isDestroyed ? Cesium.Color.fromCssColorString('#0F0C0A').withAlpha(0.88) : Cesium.Color.fromCssColorString('#2A2420').withAlpha(0.65),
                    endColor: Cesium.Color.fromCssColorString('#403830').withAlpha(0.0),
                    sizeInMeters: true,
                    imageSize: new Cesium.Cartesian2(isDestroyed ? 4.5 : 3.0, isDestroyed ? 4.5 : 3.0),
                    startScale: 1.0,
                    endScale: isDestroyed ? 3.5 : 2.5,
                    minimumParticleLife: 1.5,
                    maximumParticleLife: 3.2,
                    minimumSpeed: 2.0,
                    maximumSpeed: isDestroyed ? 6.0 : 4.0,
                    emissionRate: isDestroyed ? 12 : 8,
                    lifetime: 45.0,
                    loop: false,
                    emitter: new Cesium.ConeEmitter(Cesium.Math.toRadians(15.0)),
                    modelMatrix: posMatrix,
                    updateCallback: function(p, dt) {
                        Cesium.Cartesian3.multiplyByScalar(upVector, (isDestroyed ? 8.0 : 5.0) * dt, scratchVec);
                        p.velocity = Cesium.Cartesian3.add(p.velocity, scratchVec, p.velocity);
                    }
                });
                viewer.scene.primitives.add(smokePS);
                buildingRuinParticles.push(smokePS);

                // 2. If destroyed, add smoldering embers / fire sparks
                if (isDestroyed) {
                    if (buildingRuinParticles.length >= 8) {
                        var oldPS2 = buildingRuinParticles.shift();
                        try { viewer.scene.primitives.remove(oldPS2); } catch(e) {}
                    }
                    var sparkPS = new Cesium.ParticleSystem({
                        image: getSparkParticleTexture(),
                        startColor: Cesium.Color.fromCssColorString('#FF9900').withAlpha(0.9),
                        endColor: Cesium.Color.fromCssColorString('#FF2200').withAlpha(0.0),
                        sizeInMeters: true,
                        imageSize: new Cesium.Cartesian2(0.6, 0.6),
                        startScale: 1.0,
                        endScale: 0.3,
                        minimumParticleLife: 0.8,
                        maximumParticleLife: 1.6,
                        minimumSpeed: 3.0,
                        maximumSpeed: 8.0,
                        emissionRate: 5,
                        lifetime: 25.0,
                        loop: false,
                        emitter: new Cesium.SphereEmitter(1.5),
                        modelMatrix: posMatrix,
                        updateCallback: function(p, dt) {
                            Cesium.Cartesian3.multiplyByScalar(upVector, 4.0 * dt, scratchVec);
                            p.velocity = Cesium.Cartesian3.add(p.velocity, scratchVec, p.velocity);
                        }
                    });
                    viewer.scene.primitives.add(sparkPS);
                    buildingRuinParticles.push(sparkPS);
                }
            }

            function clearBuildingRuinParticles() {
                for (var i = 0; i < buildingRuinParticles.length; i++) {
                    try {
                        viewer.scene.primitives.remove(buildingRuinParticles[i]);
                    } catch(e) {}
                }
                buildingRuinParticles = [];
            }

            function setObjHeightInternal(obj, h) {
                obj.height = h;
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
            }

            function modifyObjColorInternal(obj, hexColor) {
                var rgb = hexToRgb(hexColor);
                obj.matArr = rgb;
                obj.colorHex = hexColor;
                var cesColor = new Cesium.Color(rgb[0], rgb[1], rgb[2], 1.0);
                if (obj.type === 'box' && obj.entity.box) obj.entity.box.material = cesColor;
                else if ((obj.type === 'cylinder' || obj.type === 'cone') && obj.entity.cylinder) obj.entity.cylinder.material = cesColor;
                else if (obj.type === 'sphere' && obj.entity.ellipsoid) obj.entity.ellipsoid.material = cesColor;
                else if (obj.type === 'polygon' && obj.entity.polygon) obj.entity.polygon.material = cesColor;
            }

            function setObjOutlineColorInternal(obj, hexColor) {
                var rgb = hexToRgb(hexColor);
                obj.outArr = rgb;
                var cesOut = new Cesium.Color(rgb[0], rgb[1], rgb[2], 1.0);
                if (obj.type === 'box' && obj.entity.box) { obj.entity.box.outline = true; obj.entity.box.outlineColor = cesOut; }
                else if ((obj.type === 'cylinder' || obj.type === 'cone') && obj.entity.cylinder) { obj.entity.cylinder.outline = true; obj.entity.cylinder.outlineColor = cesOut; }
                else if (obj.type === 'sphere' && obj.entity.ellipsoid) { obj.entity.ellipsoid.outline = true; obj.entity.ellipsoid.outlineColor = cesOut; }
                else if (obj.type === 'polygon' && obj.entity.polygon) { obj.entity.polygon.outline = true; obj.entity.polygon.outlineColor = cesOut; }
            }

            function applyDamageToCustomObjects(blastPos, rRed, rOrange, rYellow, currentRadius) {
                // Condition for building damage inside blast radius removed per user request
                return;
            }

            window.repairSingleBuilding = function(id) {
                var obj = objectRegistry.find(function(o) { return o.id === id; });
                if (!obj || !obj._originalState) return;

                var orig = obj._originalState;
                setObjHeightInternal(obj, orig.height);
                modifyObjColorInternal(obj, orig.colorHex);
                setObjOutlineColorInternal(obj, rgbToHex(orig.outArr[0], orig.outArr[1], orig.outArr[2]));

                obj.damageLevel = 'INTACT';
                obj.damagePercent = 0;
                if (obj.lblEnt && obj.lblEnt.label) {
                    obj.lblEnt.label.text = (SCFG[obj.type] ? SCFG[obj.type].icon : '🏢') + ' ' + orig.name;
                    obj.lblEnt.label.fillColor = Cesium.Color.WHITE;
                }

                if (selectedObjectId === id) {
                    openObjectControlBar(obj);
                }
                syncDataToQt();
            };

            window.repairAllBuildings = function() {
                clearBuildingRuinParticles();
                for (var i = 0; i < objectRegistry.length; i++) {
                    var obj = objectRegistry[i];
                    if (obj && obj._originalState) {
                        var orig = obj._originalState;
                        setObjHeightInternal(obj, orig.height);
                        modifyObjColorInternal(obj, orig.colorHex);
                        setObjOutlineColorInternal(obj, rgbToHex(orig.outArr[0], orig.outArr[1], orig.outArr[2]));
                        obj.damageLevel = 'INTACT';
                        obj.damagePercent = 0;
                        if (obj.lblEnt && obj.lblEnt.label) {
                            obj.lblEnt.label.text = (SCFG[obj.type] ? SCFG[obj.type].icon : '🏢') + ' ' + orig.name;
                            obj.lblEnt.label.fillColor = Cesium.Color.WHITE;
                        }
                    } else if (obj) {
                        obj.damageLevel = 'INTACT';
                        obj.damagePercent = 0;
                    }
                }

                if (selectedObjectId !== null) {
                    var sel = objectRegistry.find(function(o) { return o.id === selectedObjectId; });
                    if (sel) openObjectControlBar(sel);
                }

                // Reset OSM Buildings damage shader
                if (window.osmBuildingsTileset) {
                    window.osmBuildingsTileset.customShader = null;
                }
                osmDamageShader = null;

                syncDataToQt();
            };

            window.toggleDamageMode = function() {
                buildingDamageEnabled = false;
                repairAllBuildings();
            };

            function triggerCameraShake(intensity, durationMs) {
                if (!viewer || !viewer.camera) return;
                if (window._isRecordingVideo) return; // Maintain smooth, perfectly centered orbit during video recording
                var startTime = performance.now();
                var baseInt = intensity || 32;
                var dur = durationMs || 900;
                function frame() {
                    var elapsed = performance.now() - startTime;
                    if (elapsed < dur) {
                        var p = elapsed / dur;
                        var decay = Math.pow(1.0 - p, 2.8);
                        var mag = baseInt * decay;
                        var freq = elapsed * 0.065;
                        var dx = (Math.sin(freq) * 0.7 + (Math.random() - 0.5) * 0.6) * mag;
                        var dy = (Math.cos(freq * 1.3) * 0.7 + (Math.random() - 0.5) * 0.6) * mag;
                        viewer.camera.moveRight(dx);
                        viewer.camera.moveUp(dy);
                        requestAnimationFrame(frame);
                    }
                }
                requestAnimationFrame(frame);
            }

            function getCirclePositions(centerCartesian, radiusMeters, numPoints) {
                numPoints = numPoints || 64;
                var positions = [];
                var carto = Cesium.Cartographic.fromCartesian(centerCartesian);
                var lat = carto.latitude;
                var lon = carto.longitude;
                var rLat = radiusMeters / 6378137.0;
                var rLon = radiusMeters / (6378137.0 * Math.cos(lat));
                for (var i = 0; i <= numPoints; i++) {
                    var theta = (i / numPoints) * 2.0 * Math.PI;
                    positions.push(Cesium.Cartesian3.fromRadians(
                        lon + rLon * Math.cos(theta),
                        lat + rLat * Math.sin(theta),
                        0
                    ));
                }
                return positions;
            }

            // =================================================================
            // ULTRA-REALISTIC EXPLOSION SIMULATION ENGINE (CESIUM PARTICLE SYSTEMS)
            // =================================================================
            function playExplosionAnimation(pos, groundPos, rRed, rOrange, rYellow, wName, targets, onComplete) {
                if (currentAnimController && typeof currentAnimController.stop === 'function') {
                    currentAnimController.stop();
                }
                closePinControlBar();
                closeObjectControlBar();
                closeImageControlBar();

                var totalDuration = 2600 / animSpeed;
                var startTime = performance.now();
                var isStopped = false;

                // 📳 Visceral Camera Shockwave Impulse
                triggerCameraShake(36, 950 / animSpeed);

                var scaleFactor = Math.max(0.85, Math.min(3.5, rRed / 10.0));
                var posMatrix = Cesium.Transforms.eastNorthUpToFixedFrame(pos);
                var groundMatrix = Cesium.Transforms.eastNorthUpToFixedFrame(groundPos);
                var upVector = Cesium.Ellipsoid.WGS84.geodeticSurfaceNormal(pos);
                var scratchVec = new Cesium.Cartesian3();

                // 1. ⚡ White-Hot Flash Center Point (แสงวาบสว่างจ้าศูนย์กลางระเบิด)
                var flashEntity = viewer.entities.add({
                    position: pos,
                    point: {
                        pixelSize: new Cesium.CallbackProperty(function() {
                            var elapsed = performance.now() - startTime;
                            var p = Math.min(1.0, elapsed / (220 / animSpeed));
                            return (1 - p) * 36;
                        }, false),
                        color: new Cesium.CallbackProperty(function() {
                            var elapsed = performance.now() - startTime;
                            var p = Math.min(1.0, elapsed / (220 / animSpeed));
                            return Cesium.Color.WHITE.withAlpha((1 - p) * 0.95);
                        }, false),
                        disableDepthTestDistance: Number.POSITIVE_INFINITY
                    }
                });

                // 2. 🔥 Layer A: Incandescent Fireball Particle System (ลูกไฟระเบิดพวยพุ่งในขนาดเมตริกจริง 3 มิติ ไม่ลอยบังหน้าจอ)
                var fireballPS = new Cesium.ParticleSystem({
                    image: getFireParticleTexture(),
                    startColor: Cesium.Color.WHITE,
                    endColor: Cesium.Color.fromCssColorString('#6E0F05').withAlpha(0.0),
                    sizeInMeters: true,
                    imageSize: new Cesium.Cartesian2(Math.max(3.5, rRed * 0.4), Math.max(3.5, rRed * 0.4)),
                    startScale: 1.0,
                    endScale: 2.8,
                    minimumParticleLife: 0.55 / animSpeed,
                    maximumParticleLife: 1.15 / animSpeed,
                    minimumSpeed: 5.0,
                    maximumSpeed: 16.0,
                    emissionRate: 90,
                    bursts: [
                        new Cesium.ParticleBurst({ time: 0.0, minimum: 60, maximum: 90 }),
                        new Cesium.ParticleBurst({ time: 0.08 / animSpeed, minimum: 30, maximum: 50 }),
                        new Cesium.ParticleBurst({ time: 0.16 / animSpeed, minimum: 15, maximum: 30 })
                    ],
                    lifetime: 1.15 / animSpeed,
                    loop: false,
                    emitter: new Cesium.SphereEmitter(Math.max(1.5, rRed * 0.25)),
                    modelMatrix: posMatrix,
                    updateCallback: function(p, dt) {
                        // Upward thermal buoyancy on fire tongues
                        Cesium.Cartesian3.multiplyByScalar(upVector, 16.0 * dt, scratchVec);
                        p.velocity = Cesium.Cartesian3.add(p.velocity, scratchVec, p.velocity);
                    }
                });
                viewer.scene.primitives.add(fireballPS);

                // 3. ✨ Layer B: Fiery Sparks & Ballistic Debris (สะเก็ดไฟและเศษซากพุ่งวิถีโค้ง)
                var sparkPS = new Cesium.ParticleSystem({
                    image: getSparkParticleTexture(),
                    startColor: Cesium.Color.fromCssColorString('#FFFFAA'),
                    endColor: Cesium.Color.fromCssColorString('#FF1100').withAlpha(0.0),
                    sizeInMeters: true,
                    imageSize: new Cesium.Cartesian2(0.8, 0.8),
                    startScale: 1.2,
                    endScale: 0.2,
                    minimumParticleLife: 0.8 / animSpeed,
                    maximumParticleLife: 1.8 / animSpeed,
                    minimumSpeed: 20.0,
                    maximumSpeed: 55.0,
                    emissionRate: 0,
                    bursts: [
                        new Cesium.ParticleBurst({ time: 0.0, minimum: 60, maximum: 90 })
                    ],
                    lifetime: 1.8 / animSpeed,
                    loop: false,
                    emitter: new Cesium.ConeEmitter(Cesium.Math.toRadians(65.0)),
                    modelMatrix: posMatrix,
                    updateCallback: function(p, dt) {
                        // Gravity pulling flying fragments down in arcs
                        Cesium.Cartesian3.multiplyByScalar(upVector, -28.0 * dt, scratchVec);
                        p.velocity = Cesium.Cartesian3.add(p.velocity, scratchVec, p.velocity);
                    }
                });
                viewer.scene.primitives.add(sparkPS);

                // 4. 🌋 Layer C: Billowing Volumetric Mushroom Cloud (เสาควันและกลุ่มควันเห็ดม้วนตัวลอยขึ้นฟ้า)
                var smokePS = new Cesium.ParticleSystem({
                    image: getSmokeParticleTexture(),
                    startColor: Cesium.Color.fromCssColorString('#14100D').withAlpha(0.92),
                    endColor: Cesium.Color.fromCssColorString('#3A322C').withAlpha(0.0),
                    sizeInMeters: true,
                    imageSize: new Cesium.Cartesian2(Math.max(4.5, rRed * 0.5), Math.max(4.5, rRed * 0.5)),
                    startScale: 1.0,
                    endScale: 4.0,
                    minimumParticleLife: 1.8 / animSpeed,
                    maximumParticleLife: 3.6 / animSpeed,
                    minimumSpeed: 8.0,
                    maximumSpeed: 20.0,
                    emissionRate: 40,
                    bursts: [
                        new Cesium.ParticleBurst({ time: 0.06 / animSpeed, minimum: 35, maximum: 55 })
                    ],
                    lifetime: 2.8 / animSpeed,
                    loop: false,
                    emitter: new Cesium.ConeEmitter(Cesium.Math.toRadians(20.0)),
                    modelMatrix: posMatrix,
                    updateCallback: function(p, dt) {
                        // Strong thermal chimney updraft
                        Cesium.Cartesian3.multiplyByScalar(upVector, 22.0 * dt, scratchVec);
                        p.velocity = Cesium.Cartesian3.add(p.velocity, scratchVec, p.velocity);
                    }
                });
                viewer.scene.primitives.add(smokePS);

                // 5. 💨 Layer D: Supersonic Ground Blast Wind & Base Surge (คลื่นฝุ่นลมกรรโชกแนบผิวดิน)
                var dustWavePS = new Cesium.ParticleSystem({
                    image: getDustParticleTexture(),
                    startColor: Cesium.Color.fromCssColorString('#C8B49B').withAlpha(0.65),
                    endColor: Cesium.Color.fromCssColorString('#706050').withAlpha(0.0),
                    sizeInMeters: true,
                    imageSize: new Cesium.Cartesian2(Math.max(5.5, rRed * 0.55), Math.max(5.5, rRed * 0.55)),
                    startScale: 1.0,
                    endScale: 3.2,
                    minimumParticleLife: 1.2 / animSpeed,
                    maximumParticleLife: 2.2 / animSpeed,
                    minimumSpeed: 18.0,
                    maximumSpeed: 45.0,
                    emissionRate: 0,
                    bursts: [
                        new Cesium.ParticleBurst({ time: 0.04 / animSpeed, minimum: 50, maximum: 80 })
                    ],
                    lifetime: 2.2 / animSpeed,
                    loop: false,
                    emitter: new Cesium.CircleEmitter(Math.max(2.5, rRed * 0.3)),
                    modelMatrix: posMatrix,
                    updateCallback: function(p, dt) {
                        // Atmospheric drag deceleration
                        p.velocity = Cesium.Cartesian3.multiplyByScalar(p.velocity, Math.max(0.1, 1.0 - 0.60 * dt), p.velocity);
                    }
                });
                viewer.scene.primitives.add(dustWavePS);

                var curRadius = 1;
                var curColor = Cesium.Color.RED;
                var curAlpha = 0.65;
                var windRadius = 1;
                var windAlpha = 0.4;

                // 6. 💨 Supersonic Ground Shockwave Ring Clamped to Terrain (คลื่นกระแทกแนบผิวดิน 100% ไม่ลอยและไม่บดบังท้องฟ้า)
                var groundShockwaveRing = viewer.entities.add({
                    polyline: {
                        positions: new Cesium.CallbackProperty(function() {
                            return getCirclePositions(pos, curRadius, 64);
                        }, false),
                        width: 5.0,
                        material: new Cesium.ColorMaterialProperty(new Cesium.CallbackProperty(function() {
                            return curColor.withAlpha(Math.min(1.0, curAlpha * 1.4));
                        }, false)),
                        clampToGround: true
                    }
                });

                // 8. Scorched Ground Crater Decal (รอยไหม้เกรียมบนผิวดินหลุมระเบิด)
                var craterDecal = viewer.entities.add({
                    position: groundPos,
                    ellipse: {
                        semiMajorAxis: rRed * 0.95,
                        semiMinorAxis: rRed * 0.95,
                        material: Cesium.Color.fromCssColorString('#120904').withAlpha(0.78),
                        classificationType: Cesium.ClassificationType.BOTH
                    },
                    show: false
                });

                var particleSystems = [fireballPS, sparkPS, smokePS, dustWavePS];
                var tempEntities = [flashEntity, groundShockwaveRing, craterDecal];

                currentAnimController = {
                    stop: function() {
                        isStopped = true;
                        for (var i = 0; i < particleSystems.length; i++) {
                            try {
                                viewer.scene.primitives.remove(particleSystems[i]);
                            } catch(e) {}
                        }
                        for (var j = 0; j < tempEntities.length; j++) {
                            try {
                                viewer.entities.remove(tempEntities[j]);
                            } catch(e) {}
                        }
                        window.currentAnimController = null;
                        currentAnimController = null;
                    }
                };
                window.currentAnimController = currentAnimController;

                var shownRed = false;
                var shownOrange = false;
                var guideEl = document.getElementById('drawGuide');

                function step() {
                    if (isStopped) return;

                    var now = performance.now();
                    var elapsed = now - startTime;
                    var progress = Math.min(1.0, elapsed / totalDuration);

                    var windSpeed = 0;
                    var overpressure = 0;
                    var statusZoneText = '';

                    if (progress < 0.32) {
                        // Stage 1: 🔴 Lethal Fireball & Blast Wave (0.0 -> rRed)
                        var p1 = progress / 0.32;
                        var e1 = 1 - Math.pow(1 - p1, 2);
                        curRadius = Math.max(1, rRed * e1);
                        curColor = Cesium.Color.RED;
                        curAlpha = 0.70;

                        windRadius = Math.max(1, curRadius * 0.65);
                        windAlpha = 0.45;

                        windSpeed = Math.round(960 - p1 * 420);
                        overpressure = (56 - p1 * 28).toFixed(1);
                        statusZoneText = '💀 100% LETHAL FIREBALL & BLAST WAVE';
                    } else if (progress < 0.60) {
                        // เมื่อคลื่นพ้นวงแดง: เปิดการแสดงผลโซนแดงถาวร (ทั้งแผ่นพื้นดิน, เส้นขอบติด Terrain, และโดมครอบ 3D)
                        if (!shownRed && targets && targets.zoneRed) {
                            shownRed = true;
                            targets.zoneRed.groundRing.show = true;
                            if (targets.zoneRed.groundOutline) targets.zoneRed.groundOutline.show = true;
                            if (domeEnabled && targets.zoneRed.dome) targets.zoneRed.dome.show = true;
                            craterDecal.show = true;
                        }

                        // Stage 2: 🟠 Blast Wave & Overpressure (rRed -> rOrange)
                        var p2 = (progress - 0.32) / 0.28;
                        var e2 = 1 - Math.pow(1 - p2, 2);
                        curRadius = rRed + (rOrange - rRed) * e2;
                        curColor = Cesium.Color.ORANGE;
                        curAlpha = 0.50;

                        windRadius = Math.max(1, curRadius * 0.82);
                        windAlpha = 0.35;

                        windSpeed = Math.round(540 - p2 * 320);
                        overpressure = (28 - p2 * 18).toFixed(1);
                        statusZoneText = '⚠️ FATAL BLAST OVERPRESSURE & SHRAPNEL';
                    } else {
                        // เมื่อคลื่นพ้นวงส้ม: เปิดการแสดงผลโซนส้มถาวร
                        if (!shownOrange && targets && targets.zoneOrange) {
                            shownOrange = true;
                            targets.zoneOrange.groundRing.show = true;
                            if (targets.zoneOrange.groundOutline) targets.zoneOrange.groundOutline.show = true;
                            if (domeEnabled && targets.zoneOrange.dome) targets.zoneOrange.dome.show = true;
                        }

                        // Stage 3: 🟡 Fragmentation Wave & Air Blast Wind (rOrange -> rYellow)
                        var p3 = (progress - 0.60) / 0.40;
                        var e3 = 1 - Math.pow(1 - p3, 3);
                        curRadius = rOrange + (rYellow - rOrange) * e3;
                        curColor = Cesium.Color.YELLOW;
                        curAlpha = Math.max(0.05, 0.35 * (1 - p3 * 0.8));

                        windRadius = Math.max(1, curRadius * 0.88);
                        windAlpha = Math.max(0, 0.25 * (1 - p3 * 0.8));

                        windSpeed = Math.round(220 - p3 * 165);
                        overpressure = Math.max(0.8, (10 - p3 * 9.1)).toFixed(1);
                        statusZoneText = '💨 SUPERSONIC BLAST WIND & BASE SURGE';
                    }

                    if (guideEl) {
                        guideEl.style.display = 'block';
                        guideEl.innerHTML = '💥 ' + wName + ' [' + Math.round(curRadius) + 'm / ' + formatR(rYellow) + '] &nbsp;|&nbsp; ' +
                            '<span style="color:#38BDF8; font-weight:bold;">💨 WIND: ' + windSpeed + ' km/h</span> &nbsp;|&nbsp; ' +
                            '<span style="color:#FDE047;">⚡ ' + overpressure + ' PSI</span> &nbsp;|&nbsp; ' +
                            '<span style="color:' + (progress < 0.32 ? '#FF4444' : (progress < 0.60 ? '#FFA500' : '#FFFF44')) + '; font-weight:bold;">' + statusZoneText + '</span>';
                    }

                    if (progress < 1.0) {
                        requestAnimationFrame(step);
                    } else {
                        // Stage 4: คลื่นกระจายตัวสมบูรณ์ เปิดองค์ประกอบถาวรทั้งหมด (แผ่นพื้น, เส้นขอบติด Terrain 100%, และโดม 3D)
                        if (targets) {
                            if (targets.zoneRed) {
                                targets.zoneRed.groundRing.show = true;
                                if (targets.zoneRed.groundOutline) targets.zoneRed.groundOutline.show = true;
                                if (domeEnabled && targets.zoneRed.dome) targets.zoneRed.dome.show = true;
                            }
                            if (targets.zoneOrange) {
                                targets.zoneOrange.groundRing.show = true;
                                if (targets.zoneOrange.groundOutline) targets.zoneOrange.groundOutline.show = true;
                                if (domeEnabled && targets.zoneOrange.dome) targets.zoneOrange.dome.show = true;
                            }
                            if (targets.zoneYellow) {
                                targets.zoneYellow.groundRing.show = true;
                                if (targets.zoneYellow.groundOutline) targets.zoneYellow.groundOutline.show = true;
                                if (domeEnabled && targets.zoneYellow.dome) targets.zoneYellow.dome.show = true;
                            }
                            if (targets.marker) { targets.marker.show = true; }
                        }

                        // ลบ Particle Systems และองค์ประกอบชั่วคราว
                        for (var pIdx = 0; pIdx < particleSystems.length; pIdx++) {
                            try {
                                viewer.scene.primitives.remove(particleSystems[pIdx]);
                            } catch(e) {}
                        }
                        for (var k = 0; k < tempEntities.length; k++) {
                            try {
                                viewer.entities.remove(tempEntities[k]);
                            } catch(e) {}
                        }

                        if (typeof onComplete === 'function') onComplete();

                        // 🔁 ตรวจสอบโหมดเล่นวนลูป (Loop Mode)
                        if (animLoop && !isStopped) {
                            if (guideEl) {
                                guideEl.innerHTML = '🔁 <b>LOOP MODE ACTIVE</b>: Replaying blast in <span style="color:#38BDF8;">1.2s</span>... (กด [LOOP: OFF] หรือ [STOP] เพื่อหยุด)';
                            }
                            animLoopTimer = setTimeout(function() {
                                if (animLoop && !isStopped) {
                                    replayActivePinAnim();
                                }
                            }, 1200 / animSpeed);
                        } else {
                            if (guideEl) {
                                guideEl.innerHTML = '🎯 <b>Detonation Complete</b>: ' + wName + ' [🔴' + formatR(rRed) + ' 🟠' + formatR(rOrange) + ' 🟡' + formatR(rYellow) + ']';
                                setTimeout(function() {
                                    if (!isDrawing && !animLoop) guideEl.style.display = 'none';
                                }, 1500);
                            }
                        }
                    }
                }

                requestAnimationFrame(step);
            }

            // =================================================================
            // MULTI-PIN CLUSTER BLAST RADIUS EXPANSION & LOOP ENGINE
            // ฟังก์ชันอนิเมชันคลื่นแรงอัดระเบิดขยายตัวพร้อมกันทุกจุดในคลัสเตอร์ และเล่นวนลูปอย่างต่อเนื่อง
            // =================================================================
            window.playMultiPinBlastAnimation = function(pins, isLoop, onComplete) {
                if (!pins || pins.length === 0) return;

                if (currentAnimController && typeof currentAnimController.stop === 'function') {
                    currentAnimController.stop();
                    currentAnimController = null;
                }
                if (animLoopTimer) {
                    clearTimeout(animLoopTimer);
                    animLoopTimer = null;
                }

                closePinControlBar();
                closeObjectControlBar();
                closeImageControlBar();

                var isStopped = false;
                var cycleDuration = 3200 / animSpeed;
                var startTime = performance.now();

                // 1. ซ่อนวงรัศมี (0..8) ของทุกหมุดในคลัสเตอร์ เพื่อเริ่มอนิเมชันคลื่นระเบิดใหม่ คงหมุดและแบดจ์ (9) ไว้
                for (var pi = 0; pi < pins.length; pi++) {
                    var p = pins[pi];
                    if (p && p.entities) {
                        for (var ei = 0; ei < 9; ei++) {
                            if (p.entities[ei]) p.entities[ei].show = false;
                        }
                        if (p.entities[9]) p.entities[9].show = true;
                    }
                }

                // 2. ส่งเสียงระเบิดและแรงสั่นสะเทือนกล้อง
                playExplosionSound();
                triggerCameraShake(32, 850 / animSpeed);

                // 3. สร้างวงคลื่นกระแทกแนบผิวดิน (Supersonic Shockwave Rings) และอนุภาคไฟสำหรับแต่ละหมุด
                var tempEntities = [];
                var particleSystems = [];
                var pinTrackers = [];

                for (var i = 0; i < pins.length; i++) {
                    (function(pin) {
                        var pPos = pin.cartesian || Cesium.Cartesian3.fromDegrees(pin.lon, pin.lat, pin.alt || 0);
                        var curR = 1;
                        var curC = Cesium.Color.RED;
                        var curA = 0.70;

                        var shockRing = viewer.entities.add({
                            polyline: {
                                positions: new Cesium.CallbackProperty(function() {
                                    return getCirclePositions(pPos, curR, 54);
                                }, false),
                                width: 5.0,
                                material: new Cesium.ColorMaterialProperty(new Cesium.CallbackProperty(function() {
                                    return curC.withAlpha(Math.min(1.0, curA * 1.4));
                                }, false)),
                                clampToGround: true
                            }
                        });
                        tempEntities.push(shockRing);

                        var flash = viewer.entities.add({
                            position: pPos,
                            point: {
                                pixelSize: new Cesium.CallbackProperty(function() {
                                    var elapsed = performance.now() - startTime;
                                    var pRatio = Math.min(1.0, elapsed / (220 / animSpeed));
                                    return (1 - pRatio) * 36;
                                }, false),
                                color: Cesium.Color.WHITE.withAlpha(0.95),
                                disableDepthTestDistance: Number.POSITIVE_INFINITY
                            }
                        });
                        tempEntities.push(flash);

                        // Fireball particles for first 4 pins in cluster
                        if (i < 4) {
                            try {
                                var pMatrix = Cesium.Transforms.eastNorthUpToFixedFrame(pPos);
                                var pUp = Cesium.Ellipsoid.WGS84.geodeticSurfaceNormal(pPos);
                                var pScratch = new Cesium.Cartesian3();
                                var fbPS = new Cesium.ParticleSystem({
                                    image: getFireParticleTexture(),
                                    startColor: Cesium.Color.WHITE,
                                    endColor: Cesium.Color.fromCssColorString('#6E0F05').withAlpha(0.0),
                                    sizeInMeters: true,
                                    imageSize: new Cesium.Cartesian2(Math.max(3.5, (pin.rRed || 25) * 0.4), Math.max(3.5, (pin.rRed || 25) * 0.4)),
                                    startScale: 1.0,
                                    endScale: 2.8,
                                    minimumParticleLife: 0.55 / animSpeed,
                                    maximumParticleLife: 1.15 / animSpeed,
                                    minimumSpeed: 5.0,
                                    maximumSpeed: 16.0,
                                    emissionRate: 60,
                                    bursts: [
                                        new Cesium.ParticleBurst({ time: 0.0, minimum: 40, maximum: 60 })
                                    ],
                                    lifetime: 1.15 / animSpeed,
                                    loop: false,
                                    emitter: new Cesium.SphereEmitter(Math.max(1.5, (pin.rRed || 25) * 0.25)),
                                    modelMatrix: pMatrix,
                                    updateCallback: function(p, dt) {
                                        Cesium.Cartesian3.multiplyByScalar(pUp, 16.0 * dt, pScratch);
                                        p.velocity = Cesium.Cartesian3.add(p.velocity, pScratch, p.velocity);
                                    }
                                });
                                viewer.scene.primitives.add(fbPS);
                                particleSystems.push(fbPS);
                            } catch(e) {}
                        }

                        pinTrackers.push({
                            pin: pin,
                            pos: pPos,
                            rRed: pin.rRed || 25,
                            rOrange: pin.rOrange || 50,
                            rYellow: pin.rYellow || 100,
                            setRadius: function(r, c, a) {
                                curR = r; curC = c; curA = a;
                            },
                            shownRed: false,
                            shownOrange: false
                        });
                    })(pins[i]);
                }

                var guideEl = document.getElementById('drawGuide');

                currentAnimController = {
                    stop: function() {
                        isStopped = true;
                        for (var ti = 0; ti < tempEntities.length; ti++) {
                            try { viewer.entities.remove(tempEntities[ti]); } catch(e) {}
                        }
                        tempEntities = [];
                        for (var psi = 0; psi < particleSystems.length; psi++) {
                            try { viewer.scene.primitives.remove(particleSystems[psi]); } catch(e) {}
                        }
                        particleSystems = [];
                        window.currentAnimController = null;
                        currentAnimController = null;
                    }
                };
                window.currentAnimController = currentAnimController;

                function step() {
                    if (isStopped) return;

                    var now = performance.now();
                    var elapsed = now - startTime;
                    var progress = Math.min(1.0, elapsed / cycleDuration);

                    for (var k = 0; k < pinTrackers.length; k++) {
                        var pt = pinTrackers[k];
                        var p = pt.pin;

                        if (progress < 0.32) {
                            var p1 = progress / 0.32;
                            var e1 = 1 - Math.pow(1 - p1, 2);
                            pt.setRadius(Math.max(1, pt.rRed * e1), Cesium.Color.RED, 0.70);
                        } else if (progress < 0.60) {
                            if (!pt.shownRed) {
                                pt.shownRed = true;
                                if (p.entities[6]) p.entities[6].show = true;
                                if (p.entities[7]) p.entities[7].show = true;
                                if (domeEnabled && p.entities[8]) p.entities[8].show = true;
                            }
                            var p2 = (progress - 0.32) / 0.28;
                            var e2 = 1 - Math.pow(1 - p2, 2);
                            pt.setRadius(pt.rRed + (pt.rOrange - pt.rRed) * e2, Cesium.Color.ORANGE, 0.50);
                        } else {
                            if (!pt.shownOrange) {
                                pt.shownOrange = true;
                                if (p.entities[3]) p.entities[3].show = true;
                                if (p.entities[4]) p.entities[4].show = true;
                                if (domeEnabled && p.entities[5]) p.entities[5].show = true;
                            }
                            var p3 = (progress - 0.60) / 0.40;
                            var e3 = 1 - Math.pow(1 - p3, 3);
                            var a3 = Math.max(0.05, 0.35 * (1 - p3 * 0.8));
                            pt.setRadius(pt.rOrange + (pt.rYellow - pt.rOrange) * e3, Cesium.Color.YELLOW, a3);
                        }
                    }

                    if (guideEl && !window._isRecordingVideo) {
                        guideEl.style.display = 'block';
                        guideEl.innerHTML = '💥 <b>CLUSTER BLAST SIMULATION</b>: ' + pins.length + ' Targets &nbsp;|&nbsp; ' +
                            '<span style="color:' + (progress < 0.32 ? '#FF4444' : (progress < 0.60 ? '#FFA500' : '#FFFF44')) + '; font-weight:bold;">' +
                            (progress < 0.32 ? '🔴 LETHAL EXPANSION' : (progress < 0.60 ? '🟠 OVERPRESSURE PROPAGATION' : '🟡 FRAGMENTATION SURGE')) + '</span>';
                    }

                    if (progress < 1.0) {
                        requestAnimationFrame(step);
                    } else {
                        // Stage 4: แสดงวงรอบนอกสีเหลืองและโดมครอบถาวรของทุกจุด
                        for (var m = 0; m < pins.length; m++) {
                            var finP = pins[m];
                            if (finP && finP.entities) {
                                for (var ei = 0; ei < 9; ei++) {
                                    if (finP.entities[ei]) {
                                        finP.entities[ei].show = finP.entities[ei]._isDome ? !!domeEnabled : true;
                                    }
                                }
                            }
                        }

                        // ลบวงคลื่นชั่วคราว
                        for (var ti = 0; ti < tempEntities.length; ti++) {
                            try { viewer.entities.remove(tempEntities[ti]); } catch(e) {}
                        }
                        tempEntities = [];
                        for (var psi = 0; psi < particleSystems.length; psi++) {
                            try { viewer.scene.primitives.remove(particleSystems[psi]); } catch(e) {}
                        }
                        particleSystems = [];
                        currentAnimController = null;

                        if (typeof onComplete === 'function') onComplete();

                        // 🔁 ตรวจสอบการเล่นวนลูป
                        if (isLoop && !isStopped) {
                            if (guideEl && !window._isRecordingVideo) {
                                guideEl.innerHTML = '🔁 <b>LOOP MODE ACTIVE</b>: Replaying cluster blast in <span style="color:#38BDF8;">1.2s</span>...';
                            }
                            animLoopTimer = setTimeout(function() {
                                if (!isStopped && (animLoop || (isLoop && window._isRecordingVideo))) {
                                    playMultiPinBlastAnimation(pins, isLoop, onComplete);
                                }
                            }, 1200 / animSpeed);
                        } else {
                            if (guideEl && !window._isRecordingVideo) {
                                setTimeout(function() {
                                    if (!isDrawing && !animLoop) guideEl.style.display = 'none';
                                }, 1500);
                            }
                        }
                    }
                }

                requestAnimationFrame(step);
            };

            window.replayActivePinAnim = function() {
                if (window.pinRegistry && window.pinRegistry.length > 1) {
                    playMultiPinBlastAnimation(window.pinRegistry, animLoop);
                    return;
                }
                if (selectedPinId === null || !pinRegistry.find(function(item) { return item.id === selectedPinId; })) {
                    if (window.pinRegistry && window.pinRegistry.length > 0) {
                        selectedPinId = window.pinRegistry[window.pinRegistry.length - 1].id;
                        selectPin(selectedPinId);
                    } else {
                        // ถ้ายังไม่มีหมุดเลย ให้สร้างเป้าหมายที่จุดกึ่งกลางมุมมองปัจจุบันทันที
                        var canvas = viewer.scene.canvas;
                        var screenCenter = new Cesium.Cartesian2(canvas.clientWidth / 2, canvas.clientHeight / 2);
                        var ray = viewer.camera.getPickRay(screenCenter);
                        var center = null;
                        if (ray) {
                            try { center = viewer.scene.globe.pick(ray, viewer.scene); } catch(e) {}
                        }
                        if (!center) {
                            try { center = viewer.camera.pickEllipsoid(screenCenter, viewer.scene.globe.ellipsoid); } catch(e) {}
                        }
                        var cLat = 13.7563, cLon = 100.5018, cAlt = 0;
                        if (center) {
                            var carto = Cesium.Cartographic.fromCartesian(center);
                            cLat = Cesium.Math.toDegrees(carto.latitude);
                            cLon = Cesium.Math.toDegrees(carto.longitude);
                            try {
                                var h = viewer.scene.globe.getHeight(carto);
                                if (typeof h === 'number' && !isNaN(h)) cAlt = h;
                                else if (typeof carto.height === 'number') cAlt = carto.height;
                            } catch(e) { cAlt = carto.height || 0; }
                        }
                        addPin(cLat, cLon, tacticalRadiusConfig.label, tacticalRadiusConfig.rRed, tacticalRadiusConfig.rOrange, tacticalRadiusConfig.rYellow, cAlt);
                        return;
                    }
                }
                var p = pinRegistry.find(function(item) { return item.id === selectedPinId; });
                if (!p || !p.entities || p.entities.length < 7) {
                    reportStatus('LOG', 'Pin entities not ready for replay.');
                    return;
                }

                var pos = Cesium.Cartesian3.fromDegrees(p.lon, p.lat, p.alt || 0);
                var groundPos = pos;

                // ตรวจสอบว่าเป้าหมายอยู่ในสายตาหรือไม่ ถ้าอยู่นอกจอหรือไกลเกินไป ให้จัดมุมมองกล้องอย่างนุ่มนวล
                var canvas = viewer.scene.canvas;
                var sc = Cesium.SceneTransforms.wgs84ToWindowCoordinates(viewer.scene, pos);
                var isOffScreen = !sc || sc.x < 50 || sc.x > (canvas.clientWidth - 50) || sc.y < 50 || sc.y > (canvas.clientHeight - 50);
                var camDist = Cesium.Cartesian3.distance(viewer.camera.position, pos);

                function runReplayBlast() {
                    closePinControlBar();
                    for (var i = 0; i < p.entities.length; i++) {
                        p.entities[i].show = false;
                    }

                    // ฟื้นฟูสภาพตึกในรัศมีเป้าหมายชั่วคราว เพื่อให้เห็นอนิเมชั่นการพังทลายอย่างชัดเจนอีกครั้ง
                    for (var b = 0; b < objectRegistry.length; b++) {
                        var obj = objectRegistry[b];
                        if (obj && obj._originalState) {
                            var objPos = Cesium.Cartesian3.fromDegrees(obj.lon, obj.lat, obj.th || 0);
                            if (Cesium.Cartesian3.distance(pos, objPos) <= p.rYellow) {
                                var orig = obj._originalState;
                                setObjHeightInternal(obj, orig.height);
                                modifyObjColorInternal(obj, orig.colorHex);
                                setObjOutlineColorInternal(obj, rgbToHex(orig.outArr[0], orig.outArr[1], orig.outArr[2]));
                                obj.damageLevel = 'INTACT';
                                obj.damagePercent = 0;
                                if (obj.lblEnt && obj.lblEnt.label) {
                                    obj.lblEnt.label.text = (SCFG[obj.type] ? SCFG[obj.type].icon : '🏢') + ' ' + orig.name;
                                    obj.lblEnt.label.fillColor = Cesium.Color.WHITE;
                                }
                            }
                        }
                    }
                    clearBuildingRuinParticles();

                    playExplosionSound();
                    var targets = {
                        pinId: p.id,
                        lat: p.lat,
                        lon: p.lon,
                        zoneYellow: { groundRing: p.entities[0], groundOutline: p.entities[1], dome: p.entities[2] },
                        zoneOrange: { groundRing: p.entities[3], groundOutline: p.entities[4], dome: p.entities[5] },
                        zoneRed: { groundRing: p.entities[6], groundOutline: p.entities[7], dome: p.entities[8] },
                        marker: p.entities[9]
                    };
                    playExplosionAnimation(pos, groundPos, p.rRed, p.rOrange, p.rYellow, p.label, targets, function() {
                        reportStatus('LOG', 'Blast Replay Finished: ' + p.label);
                        if (!animLoop) {
                            openPinControlBar(p);
                        }
                    });
                }

                if (isOffScreen || camDist > 2500) {
                    viewer.camera.flyToBoundingSphere(new Cesium.BoundingSphere(pos, 10), {
                        offset: new Cesium.HeadingPitchRange(viewer.camera.heading, Cesium.Math.toRadians(-35.0), Math.max(500, Math.min(1200, p.rYellow * 0.75))),
                        duration: 0.8,
                        complete: runReplayBlast
                    });
                } else {
                    runReplayBlast();
                }
            };

            // =========================================================================
            // 360° ORBITAL VIDEO RECORDING ENGINE (EXPORT TO MP4)
            // ฟังก์ชันบันทึกวิดีโอวงโคจร 360° รอบจุดระเบิด พร้อมอนิเมชันคลื่นแรงอัดแบบวนลูปช้าๆ
            // =========================================================================
            window._isRecordingVideo = false;
            window._activeVideoRecorder = null;
            window._videoOrbitFrameId = null;

            window.triggerVideoExportDialog = function() {
                if (!pinRegistry || pinRegistry.length === 0) {
                    alert('⚠️ ไม่พบจุดระเบิด (PIN) บนแผนที่\\n\\nกรุณาคลิกวางจุดหมุดระเบิด (PIN) บนแผนที่ก่อนเริ่มการบันทึกวิดีโอ');
                    reportStatus('ERROR', 'No tactical blast pin placed. Place a pin before exporting video.');
                    return;
                }
                if (window._isRecordingVideo) {
                    alert('⚠️ ระบบกำลังบันทึกวิดีโออยู่ กรุณารอสักครู่จนกว่าจะเสร็จสิ้น หรือกดปุ่ม CANCEL');
                    return;
                }
                // Read chosen camera export mode
                var modeSel = document.getElementById('exportOrbitMode');
                var exportMode = modeSel ? modeSel.value : 'cluster';
                // Request Python to open native file save dialog with selected mode
                reportStatus('REQUEST_VIDEO_PATH', exportMode);
            };

            window.cancelVideoRecording = function() {
                if (!window._isRecordingVideo) return;
                window._isRecordingVideo = false;
                if (window._videoOrbitFrameId) {
                    cancelAnimationFrame(window._videoOrbitFrameId);
                    window._videoOrbitFrameId = null;
                }
                if (window._activeVideoRecorder && window._activeVideoRecorder.state !== 'inactive') {
                    try {
                        window._activeVideoRecorder.stop();
                    } catch(e) {}
                }
                window._activeVideoRecorder = null;
                stopAllAnimations();
                restoreUIAfterRecording();
                reportStatus('LOG', 'Video recording cancelled by user.');
            };

            function restoreUIAfterRecording() {
                window._isRecordingVideo = false;
                window._activeVideoRecorder = null;
                if (window._videoOrbitFrameId) {
                    cancelAnimationFrame(window._videoOrbitFrameId);
                    window._videoOrbitFrameId = null;
                }
                if (animLoopTimer) {
                    clearTimeout(animLoopTimer);
                    animLoopTimer = null;
                }
                if (currentAnimController && typeof currentAnimController.stop === 'function') {
                    currentAnimController.stop();
                    currentAnimController = null;
                }
                
                // Unlock camera from orbit cleanly preserving world coordinates and view orientation
                try {
                    var curPos = viewer.camera.positionWC.clone();
                    var curDir = viewer.camera.directionWC.clone();
                    var curUp = viewer.camera.upWC.clone();
                    viewer.camera.lookAtTransform(Cesium.Matrix4.IDENTITY);
                    viewer.camera.setView({
                        destination: curPos,
                        orientation: {
                            direction: curDir,
                            up: curUp
                        }
                    });
                } catch(e) {
                    try { viewer.camera.lookAtTransform(Cesium.Matrix4.IDENTITY); } catch(ex) {}
                }
                
                // Unconditionally re-enable all mouse/touch camera controller inputs
                try {
                    var ssc = viewer.scene.screenSpaceCameraController;
                    ssc.enableInputs = true;
                    ssc.enableRotate = true;
                    ssc.enableTranslate = true;
                    ssc.enableZoom = true;
                    ssc.enableTilt = true;
                    ssc.enableLook = true;
                } catch(e) {}

                // Restore visibility of all blast zones on the map
                if (window.pinRegistry) {
                    for (var pi = 0; pi < window.pinRegistry.length; pi++) {
                        var pRef = window.pinRegistry[pi];
                        if (pRef && pRef.entities) {
                            for (var ei = 0; ei < pRef.entities.length; ei++) {
                                var ent = pRef.entities[ei];
                                if (!ent) continue;
                                if (ent._isDome) {
                                    ent.show = !!domeEnabled;
                                } else {
                                    ent.show = true;
                                }
                            }
                        }
                    }
                }

                // Hide HUDs
                var hud = document.getElementById('videoRecordingHUD');
                if (hud) hud.style.display = 'none';
                var instBtn = document.getElementById('instantShowAllBtn');
                if (instBtn) instBtn.style.display = 'none';
                window.instantShowAllRadiusAndCenter = null;
                var infoCard = document.getElementById('videoMissionInfoCard');
                if (infoCard) infoCard.style.display = 'none';

                // Re-enable button
                var expBtn = document.getElementById('exportVideoBtn');
                if (expBtn) {
                    expBtn.disabled = false;
                    expBtn.innerHTML = '🎥 EXPORT MP4';
                    expBtn.classList.remove('active');
                }
            }

            window.startVideoRecording = function(targetPath, durationSec, exportMode) {
                if (!pinRegistry || pinRegistry.length === 0) {
                    alert('⚠️ ไม่พบจุดระเบิด (PIN) บนแผนที่\\n\\nกรุณาคลิกวางจุดหมุดระเบิด (PIN) บนแผนที่ก่อนเริ่มการบันทึกวิดีโอ');
                    return;
                }
                if (window._isRecordingVideo) return;

                if (!exportMode) {
                    var modeSel = document.getElementById('exportOrbitMode');
                    exportMode = modeSel ? modeSel.value : 'cluster';
                }

                window._isRecordingVideo = true;

                // 1. Strict Conflict Suppression & Mode Safeguards:
                if (editMode) toggleEditMode(false);
                var drawer = document.getElementById('toolsDrawer');
                if (drawer) drawer.style.display = 'none';
                var tbtn = document.getElementById('toolsToggleBtn');
                if (tbtn) { tbtn.classList.remove('active'); tbtn.textContent = '🔧 3D TOOLS ▾'; }
                if (isDrawing) cancelDrawing();
                deselectAll();
                closeImageControlBar();
                closeObjectControlBar();
                closePinControlBar();
                var rCfgBox = document.getElementById('radiusConfigBox');
                if (rCfgBox) rCfgBox.style.display = 'none';

                // Stop any ongoing blast animation or loop timer
                stopAllAnimations();

                // Ensure surrounding buildings are repaired to pristine 100% so destruction can be recorded dynamically
                repairAllBuildings();

                // 2. Lock user mouse/camera controls during recording
                viewer.scene.screenSpaceCameraController.enableInputs = false;

                // Helper to safely set all blast ring and dome entity visibilities for a pin
                function setPinEntitiesVisibility(pin, visible) {
                    if (!pin || !pin.entities) return;
                    for (var i = 0; i < pin.entities.length; i++) {
                        var ent = pin.entities[i];
                        if (!ent) continue;
                        if (ent._isDome) {
                            ent.show = visible && !!domeEnabled;
                        } else {
                            ent.show = visible;
                        }
                    }
                }

                // Helper to ensure all pins across the theater have their blast rings 100% visible
                function ensureAllPinZonesVisible() {
                    if (!pinRegistry) return;
                    for (var pi = 0; pi < pinRegistry.length; pi++) {
                        setPinEntitiesVisibility(pinRegistry[pi], true);
                    }
                }

                // 3. Extract Pin Target Positions and Individual Camera Distances
                var totalPins = pinRegistry.length;
                var pinData = [];
                for (var i = 0; i < totalPins; i++) {
                    var p = pinRegistry[i];
                    var pPos = p.cartesian || Cesium.Cartesian3.fromDegrees(p.lon, p.lat, p.alt || 0);
                    var yelR = p.rYellow || 50;
                    var pDist = Math.max(120, Math.min(3500, yelR * 2.3));
                    pinData.push({
                        index: i,
                        pin: p,
                        pos: pPos,
                        dist: pDist
                    });
                }

                // Compute Centroid of all pins for the grand overview finale
                var sumX = 0, sumY = 0, sumZ = 0;
                for (var si = 0; si < totalPins; si++) {
                    sumX += pinData[si].pos.x;
                    sumY += pinData[si].pos.y;
                    sumZ += pinData[si].pos.z;
                }
                var targetCartesian = new Cesium.Cartesian3(sumX / totalPins, sumY / totalPins, sumZ / totalPins);
                try {
                    var carto = Cesium.Cartographic.fromCartesian(targetCartesian);
                    var avgAlt = 0;
                    for (var ai = 0; ai < totalPins; ai++) { avgAlt += (pinData[ai].pin.alt || 0); }
                    avgAlt /= totalPins;
                    targetCartesian = Cesium.Cartesian3.fromRadians(carto.longitude, carto.latitude, avgAlt);
                } catch(e) {}

                var maxSpan = 0;
                for (var mi = 0; mi < totalPins; mi++) {
                    var d = Cesium.Cartesian3.distance(targetCartesian, pinData[mi].pos);
                    var outer = d + (pinData[mi].pin.rYellow || 50);
                    if (outer > maxSpan) maxSpan = outer;
                }

                // Check nearby buildings to ensure overview includes all impacted structures
                var maxNearbyDist = 0;
                if (objectRegistry && objectRegistry.length > 0) {
                    for (var oi = 0; oi < objectRegistry.length; oi++) {
                        var obj = objectRegistry[oi];
                        var objPos = obj.cartesian || Cesium.Cartesian3.fromDegrees(obj.lon, obj.lat, obj.th || 0);
                        var od = Cesium.Cartesian3.distance(targetCartesian, objPos);
                        if (od <= Math.max(maxSpan * 1.8, 120) && od > maxNearbyDist) {
                            maxNearbyDist = od;
                        }
                    }
                }
                // Generous overview distance and steeper pitch to ensure ALL blast circles and targets fit 100% inside view with ample margin
                var overviewDist = Math.max(350, Math.min(10000, Math.max(maxSpan * 4.2, maxNearbyDist * 1.6)));

                // Cluster framing distance and angle for simultaneous centroid orbit
                var clusterDist = Math.max(160, Math.min(6500, Math.max(maxSpan * 3.0, maxNearbyDist * 1.35)));

                var pitchSingle = Cesium.Math.toRadians(-38.0);
                var pitchCluster = Cesium.Math.toRadians(-45.0);
                var pitchOverview = Cesium.Math.toRadians(-56.0);
                var initialHeading = 0.0;
                try {
                    var curH = viewer.camera.heading;
                    if (!isNaN(curH)) initialHeading = curH;
                } catch(e) {}

                // 4. Construct Calm, Cinematic Multi-Stage Timeline:
                var pinStages = [];
                var curHeadingAcc = initialHeading;
                var curTime = 0.0;

                if (exportMode === 'cluster' || totalPins === 1) {
                    // MODE 1: CLUSTER / SIMULTANEOUS CENTROID ORBIT (โหมดแสดงพร้อมกัน / หมุนรอบจุดกลาง)
                    // กล้องหมุนรอบจุดกลางอย่างเดียว ไม่เลื่อนไปทีละจุด แสดงจุดรัศมีระเบิดทั้งหมดทันที
                    var clusterOrbitDur = 12.0; // 12 seconds steady, graceful orbit around centroid
                    var clusterSweep = Math.PI * 1.25; // 225° smooth rotation arc

                    pinStages.push({
                        type: 'CLUSTER_ORBIT',
                        center: targetCartesian,
                        dist: clusterDist,
                        pitch: pitchCluster,
                        startHeading: curHeadingAcc,
                        headingSweep: clusterSweep,
                        startSec: curTime,
                        endSec: curTime + clusterOrbitDur,
                        duration: clusterOrbitDur,
                        detonated: true
                    });
                    curHeadingAcc += clusterSweep;
                    curTime += clusterOrbitDur;

                } else {
                    // MODE 2: SEQUENTIAL TARGET FLIGHT (โหมดบินดูทีละจุดตามลำดับ)
                    // ดูจุดแรกก่อน หมุนมุมมองอย่างนุ่มนวล พร้อมจุดระเบิด
                    // บินร่อนเปลี่ยนไปยังจุดถัดไปอย่างราบรื่น
                    // ครบทุกจุดแล้ว กล้องซูมออกให้เห็นพื้นที่วงรัศมีระเบิดทั้งหมด
                    var pinOrbitDur = (totalPins <= 2) ? 8.5 : (totalPins <= 4 ? 7.5 : 6.0);
                    var transDur = (totalPins <= 2) ? 3.5 : (totalPins <= 4 ? 3.0 : 2.5);
                    var toOverviewDur = 4.0;
                    var overviewDur = (totalPins <= 2) ? 9.0 : 8.0;

                    var orbitSweep = Math.PI * 0.90; // ~162° arc: calm, elegant, zero dizziness
                    var transSweep = Math.PI * 0.12; // ~21° subtle heading change during flight
                    var overviewSweep = Math.PI * 0.22; // ~40° slow panoramic drift over 8-9s

                    for (var k = 0; k < totalPins; k++) {
                        if (k > 0) {
                            // Smooth flight transition from pin k-1 to pin k
                            pinStages.push({
                                type: 'TRANSITION',
                                fromPos: pinData[k - 1].pos,
                                toPos: pinData[k].pos,
                                fromRange: pinData[k - 1].dist,
                                toRange: pinData[k].dist,
                                fromPitch: pitchSingle,
                                toPitch: pitchSingle,
                                fromHeading: curHeadingAcc,
                                toHeading: curHeadingAcc + transSweep,
                                startSec: curTime,
                                endSec: curTime + transDur,
                                duration: transDur,
                                targetDesc: 'MOVE_TO_PIN_' + (k + 1)
                            });
                            curHeadingAcc += transSweep;
                            curTime += transDur;
                        }

                        // Close-up cinematic arc orbit around pin k with dynamic blast explosion
                        pinStages.push({
                            type: 'PIN_ORBIT',
                            pinIdx: k,
                            center: pinData[k].pos,
                            dist: pinData[k].dist,
                            pitch: pitchSingle,
                            startHeading: curHeadingAcc,
                            headingSweep: orbitSweep,
                            startSec: curTime,
                            endSec: curTime + pinOrbitDur,
                            duration: pinOrbitDur,
                            detonated: false
                        });
                        curHeadingAcc += orbitSweep;
                        curTime += pinOrbitDur;
                    }

                    // Transition: Zoom out from last inspected pin to the tactical centroid
                    pinStages.push({
                        type: 'TRANSITION',
                        fromPos: pinData[totalPins - 1].pos,
                        toPos: targetCartesian,
                        fromRange: pinData[totalPins - 1].dist,
                        toRange: overviewDist,
                        fromPitch: pitchSingle,
                        toPitch: pitchOverview,
                        fromHeading: curHeadingAcc,
                        toHeading: curHeadingAcc + transSweep,
                        startSec: curTime,
                        endSec: curTime + toOverviewDur,
                        duration: toOverviewDur,
                        targetDesc: 'ZOOM_TO_OVERVIEW'
                    });
                    curHeadingAcc += transSweep;
                    curTime += toOverviewDur;

                    // Grand Tactical Overview Orbit: High-angle vantage showing ALL blast zones together
                    pinStages.push({
                        type: 'OVERVIEW_ORBIT',
                        center: targetCartesian,
                        dist: overviewDist,
                        pitch: pitchOverview,
                        startHeading: curHeadingAcc,
                        headingSweep: overviewSweep,
                        startSec: curTime,
                        endSec: curTime + overviewDur,
                        duration: overviewDur,
                        detonated: false
                    });
                    curHeadingAcc += overviewSweep;
                    curTime += overviewDur;
                }

                var totalSequenceDuration = curTime;
                var durationMs = totalSequenceDuration * 1000.0;

                // 5. Update UI Button and Show Top-Left Tactical HUD
                var expBtn = document.getElementById('exportVideoBtn');
                if (expBtn) {
                    expBtn.disabled = true;
                    expBtn.innerHTML = '🔴 RECORDING...';
                    expBtn.classList.add('active');
                }
                var hud = document.getElementById('videoRecordingHUD');
                if (hud) hud.style.display = 'flex';

                var instBtn = document.getElementById('instantShowAllBtn');
                if (instBtn) {
                    instBtn.style.display = (exportMode === 'sequence' && totalPins > 1) ? 'inline-block' : 'none';
                }

                var infoCard = document.getElementById('videoMissionInfoCard');
                if (infoCard) infoCard.style.display = 'block';

                function updateInfoCardForStage(st) {
                    if (!infoCard) return;
                    var html = '';
                    if (st.type === 'CLUSTER_ORBIT') {
                        html = '<div style="display:flex; align-items:center; gap:8px; margin-bottom:5px;">' +
                            '<span style="display:inline-block; width:9px; height:9px; border-radius:50%; background:#22C55E; box-shadow:0 0 10px #22C55E;"></span>' +
                            '<b style="font-size:12px; color:#F8FAFC; letter-spacing:0.5px;">🎯 CLUSTER STRIKE ASSESSMENT</b>' +
                            '</div>' +
                            '<div style="font-size:10px; color:#38BDF8; margin-bottom:6px;">MODE: SIMULTANEOUS CENTROID ORBIT &nbsp;|&nbsp; ' + totalPins + ' TARGET PINS</div>' +
                            '<div style="border-top:1px solid #334155; padding-top:6px; max-height:110px; overflow-y:auto; font-size:10px;">';
                        for (var pi = 0; pi < Math.min(4, totalPins); pi++) {
                            var cp = pinRegistry[pi];
                            html += '<div style="margin-bottom:3px;"><span style="color:#38BDF8; font-weight:bold;">#' + (pi + 1) + ' ' + (cp.label || 'POINT') + '</span>: ' +
                                '🔴' + formatR(cp.rRed) + ' 🟠' + formatR(cp.rOrange) + ' 🟡' + formatR(cp.rYellow) +
                                ' &nbsp;<span style="color:#94A3B8;">📍' + Number(cp.lat).toFixed(4) + '°, ' + Number(cp.lon).toFixed(4) + '°</span></div>';
                        }
                        if (totalPins > 4) html += '<div style="color:#94A3B8;">... and ' + (totalPins - 4) + ' more targets</div>';
                        html += '</div>';
                    } else if (st.type === 'PIN_ORBIT') {
                        var p = pinRegistry[st.pinIdx];
                        if (p) {
                            html = '<div style="display:flex; align-items:center; gap:8px; margin-bottom:5px;">' +
                                '<span style="display:inline-block; width:9px; height:9px; border-radius:50%; background:#EF4444; box-shadow:0 0 10px #EF4444;"></span>' +
                                '<b style="font-size:12px; color:#F8FAFC; letter-spacing:0.5px;">TARGET ' + (st.pinIdx + 1) + ' OF ' + totalPins + ': ' + (p.label || 'STRIKE POINT') + '</b>' +
                                '</div>' +
                                '<div style="font-size:10px; color:#38BDF8; margin-bottom:6px;">MODE: CLOSE-UP ASSESSMENT &nbsp;|&nbsp; 📍 ' + Number(p.lat).toFixed(4) + '°N, ' + Number(p.lon).toFixed(4) + '°E</div>' +
                                '<div style="border-top:1px solid #334155; padding-top:6px; font-size:11px;">' +
                                '<span style="color:#EF4444; font-weight:bold;">🔴 Lethal: ' + formatR(p.rRed) + '</span> &nbsp;&nbsp;' +
                                '<span style="color:#F97316; font-weight:bold;">🟠 Severe: ' + formatR(p.rOrange) + '</span> &nbsp;&nbsp;' +
                                '<span style="color:#EAB308; font-weight:bold;">🟡 Frag: ' + formatR(p.rYellow) + '</span>' +
                                '</div>';
                        }
                    } else if (st.type === 'TRANSITION') {
                        if (st.targetDesc === 'ZOOM_TO_OVERVIEW') {
                            html = '<div style="display:flex; align-items:center; gap:8px; margin-bottom:5px;">' +
                                '<span style="display:inline-block; width:9px; height:9px; border-radius:50%; background:#38BDF8; box-shadow:0 0 10px #38BDF8;"></span>' +
                                '<b style="font-size:12px; color:#F8FAFC; letter-spacing:0.5px;">ELEVATING TO THEATER OVERVIEW...</b>' +
                                '</div>' +
                                '<div style="font-size:10px; color:#94A3B8;">PULLING CAMERA BACK TO COMPREHENSIVE MULTI-ZONE VANTAGE</div>';
                        } else {
                            html = '<div style="display:flex; align-items:center; gap:8px; margin-bottom:5px;">' +
                                '<span style="display:inline-block; width:9px; height:9px; border-radius:50%; background:#38BDF8; box-shadow:0 0 10px #38BDF8;"></span>' +
                                '<b style="font-size:12px; color:#F8FAFC; letter-spacing:0.5px;">REPOSITIONING SENSOR POD...</b>' +
                                '</div>' +
                                '<div style="font-size:10px; color:#94A3B8;">TRANSITIONING TO NEXT STRIKE TARGET IN SEQUENCE</div>';
                        }
                    } else if (st.type === 'OVERVIEW_ORBIT') {
                        html = '<div style="display:flex; align-items:center; gap:8px; margin-bottom:5px;">' +
                            '<span style="display:inline-block; width:9px; height:9px; border-radius:50%; background:#22C55E; box-shadow:0 0 10px #22C55E;"></span>' +
                            '<b style="font-size:12px; color:#F8FAFC; letter-spacing:0.5px;">THEATER-WIDE TACTICAL OVERVIEW</b>' +
                            '</div>' +
                            '<div style="font-size:10px; color:#94A3B8; margin-bottom:6px;">ALL ' + totalPins + ' TARGET ZONES ASSESSED &nbsp;|&nbsp; MULTI-BLAST COVERAGE</div>' +
                            '<div style="border-top:1px solid #334155; padding-top:6px; max-height:110px; overflow-y:auto; font-size:10px;">';
                        for (var pi = 0; pi < Math.min(4, totalPins); pi++) {
                            var cp = pinRegistry[pi];
                            html += '<div style="margin-bottom:3px;"><span style="color:#38BDF8; font-weight:bold;">#' + (pi + 1) + ' ' + (cp.label || 'POINT') + '</span>: ' +
                                '🔴' + formatR(cp.rRed) + ' 🟠' + formatR(cp.rOrange) + ' 🟡' + formatR(cp.rYellow) +
                                ' &nbsp;<span style="color:#94A3B8;">📍' + Number(cp.lat).toFixed(4) + '°, ' + Number(cp.lon).toFixed(4) + '°</span></div>';
                        }
                        if (totalPins > 4) html += '<div style="color:#94A3B8;">... and ' + (totalPins - 4) + ' more targets</div>';
                        html += '</div>';
                    }
                    infoCard.innerHTML = html;
                }

                // 6. Canvas Stream & MediaRecorder Setup
                var canvas = viewer.scene.canvas;
                var stream = canvas.captureStream(30);
                var mimeType = '';
                var candidates = [
                    'video/webm;codecs=vp8',
                    'video/webm;codecs=vp9',
                    'video/webm',
                    'video/mp4'
                ];
                for (var mi = 0; mi < candidates.length; mi++) {
                    if (window.MediaRecorder && MediaRecorder.isTypeSupported(candidates[mi])) {
                        mimeType = candidates[mi];
                        break;
                    }
                }

                var recOptions = { videoBitsPerSecond: 8000000 };
                if (mimeType) recOptions.mimeType = mimeType;
                var recorder;
                try {
                    recorder = new MediaRecorder(stream, recOptions);
                } catch(e) {
                    recorder = new MediaRecorder(stream);
                }
                window._activeVideoRecorder = recorder;
                var recordedChunks = [];

                recorder.ondataavailable = function(e) {
                    if (e.data && e.data.size > 0) {
                        recordedChunks.push(e.data);
                    }
                };

                // Prepare metadata containing all pins' coordinates, bomb types, and radii
                var exportMetadata = {
                    totalPins: totalPins,
                    exportMode: exportMode,
                    pins: pinRegistry.map(function(p, idx) {
                        return {
                            index: idx + 1,
                            label: p.label || ('POINT #' + (idx + 1)),
                            lat: Number(p.lat).toFixed(4),
                            lon: Number(p.lon).toFixed(4),
                            alt: Math.round(p.alt || 0),
                            rRed: p.rRed,
                            rOrange: p.rOrange,
                            rYellow: p.rYellow
                        };
                    })
                };

                recorder.onstop = function() {
                    if (!window._isRecordingVideo && recordedChunks.length === 0) {
                        restoreUIAfterRecording();
                        return;
                    }
                    var finalBlob = new Blob(recordedChunks, { type: mimeType || 'video/webm' });
                    if (finalBlob.size === 0) {
                        reportStatus('ERROR', 'No video data captured (0 KB). Video export aborted.');
                        restoreUIAfterRecording();
                        return;
                    }
                    reportStatus('LOG', 'Video capture finished (' + (finalBlob.size / 1024).toFixed(1) + ' KB). Uploading to backend engine...');

                    // Prepare URL with metadata in query string
                    var metaJson = JSON.stringify(exportMetadata);
                    var postUrl = '/api/save_video_recording?path=' + encodeURIComponent(targetPath || '') + '&meta=' + encodeURIComponent(metaJson);

                    var xhr = new XMLHttpRequest();
                    xhr.open('POST', postUrl, true);
                    xhr.timeout = 300000; // 5 minutes timeout

                    if (xhr.upload) {
                        xhr.upload.onprogress = function(pe) {
                            if (pe.lengthComputable && pe.total > 0) {
                                var pct = Math.round((pe.loaded / pe.total) * 100);
                                var pBar = document.getElementById('recProgressBar');
                                var pText = document.getElementById('recProgressText');
                                if (pBar) pBar.style.width = pct + '%';
                                if (pText) pText.textContent = 'UPLOADING TO ENGINE: ' + pct + '%';
                            }
                        };
                    }

                    xhr.onload = function() {
                        try {
                            var data = JSON.parse(xhr.responseText);
                            if (xhr.status >= 200 && xhr.status < 300 && data && data.status === 'ok') {
                                reportStatus('SUCCESS', 'Exported 360° Blast MP4: ' + data.path);
                                reportStatus('VIDEO_SAVED', JSON.stringify(data));
                            } else {
                                var errMsg = (data && data.error) ? data.error : ('HTTP ' + xhr.status + ': ' + xhr.statusText);
                                reportStatus('ERROR', 'Video saving failed: ' + errMsg);
                            }
                        } catch(parseErr) {
                            reportStatus('ERROR', 'Server response error: ' + (xhr.responseText ? xhr.responseText.slice(0, 120) : ('HTTP ' + xhr.status)));
                        }
                        restoreUIAfterRecording();
                    };

                    xhr.onerror = function() {
                        reportStatus('ERROR', 'Video upload failed: Network connection error (HTTP ' + xhr.status + ')');
                        restoreUIAfterRecording();
                    };

                    xhr.ontimeout = function() {
                        reportStatus('ERROR', 'Video upload failed: Request timed out during processing');
                        restoreUIAfterRecording();
                    };

                    xhr.send(finalBlob);
                };

                // 7. Detonation Function for Target Pins
                function detonateSinglePin(idx) {
                    if (!window._isRecordingVideo) return;
                    var pin = pinRegistry[idx];
                    if (!pin) return;

                    // Hide ONLY this pin's blast rings at the moment of blast initiation
                    for (var i = 0; i < 9; i++) {
                        if (pin.entities[i]) pin.entities[i].show = false;
                    }
                    if (pin.entities[9]) pin.entities[9].show = true;

                    var targets = {
                        zoneYellow: { groundRing: pin.entities[0], groundOutline: pin.entities[1], dome: pin.entities[2] },
                        zoneOrange: { groundRing: pin.entities[3], groundOutline: pin.entities[4], dome: pin.entities[5] },
                        zoneRed: { groundRing: pin.entities[6], groundOutline: pin.entities[7], dome: pin.entities[8] },
                        marker: pin.entities[9],
                        pinId: pin.id
                    };
                    var pinGroundPos = pin.cartesian || Cesium.Cartesian3.fromDegrees(pin.lon, pin.lat, pin.alt || 0);

                    var origSpeed = animSpeed;
                    animSpeed = 0.65; // Slow, cinematic blast propagation
                    playExplosionSound();
                    playExplosionAnimation(pinGroundPos, pinGroundPos, pin.rRed, pin.rOrange, pin.rYellow, pin.label, targets, function() {
                        animSpeed = origSpeed;
                        setPinEntitiesVisibility(pin, true);
                    });
                }

                // 8. Snap Camera to First Target at t=0
                var firstStage = pinStages[0];
                var initCenter = (firstStage.type === 'PIN_ORBIT') ? firstStage.center : targetCartesian;
                var initDist = (firstStage.type === 'PIN_ORBIT') ? firstStage.dist : (firstStage.dist || clusterDist);
                var initPitch = firstStage.pitch;
                var initHeading = firstStage.startHeading;
                viewer.camera.lookAt(initCenter, new Cesium.HeadingPitchRange(initHeading, initPitch, initDist));
                try { viewer.scene.render(); } catch(e) {}

                if (exportMode === 'cluster' || totalPins === 1) {
                    // Play looping multi-pin blast shockwave expansion across all pins in cluster
                    setTimeout(function() {
                        if (window._isRecordingVideo) {
                            playMultiPinBlastAnimation(pinRegistry, true);
                        }
                    }, 350);
                } else {
                    // Sequential mode: Keep all center pin markers visible, hide blast rings until detonated
                    for (var pi = 0; pi < pinRegistry.length; pi++) {
                        var pRef = pinRegistry[pi];
                        for (var ei = 0; ei < pRef.entities.length; ei++) {
                            if (pRef.entities[ei]) pRef.entities[ei].show = false;
                        }
                        if (pRef.entities[9]) pRef.entities[9].show = true;
                    }
                }

                // Interactive button handler: Immediately show all radius rings and transition to centroid
                window.instantShowAllRadiusAndCenter = function() {
                    if (!window._isRecordingVideo) return;

                    // 1. Launch looping blast shockwave animation across all pins
                    playMultiPinBlastAnimation(pinRegistry, true);

                    // 2. Hide button so it cannot be triggered repeatedly
                    var instBtn = document.getElementById('instantShowAllBtn');
                    if (instBtn) instBtn.style.display = 'none';

                    // 4. Smoothly divert camera immediately to centroid orbit
                    var nowSec = (performance.now() - startTime) / 1000.0;
                    var transDur = 2.0;
                    var clusterRemainDur = 8.0;

                    // Find camera current position / heading
                    var curFromCenter = targetCartesian;
                    var curFromDist = clusterDist;
                    var curFromPitch = pitchSingle;
                    var curFromHeading = initialHeading;

                    for (var si = 0; si < pinStages.length; si++) {
                        var s = pinStages[si];
                        if (nowSec >= s.startSec && (nowSec < s.endSec || si === pinStages.length - 1)) {
                            if (s.type === 'PIN_ORBIT') {
                                curFromCenter = s.center;
                                curFromDist = s.dist;
                                curFromPitch = s.pitch;
                                var localT = Math.min(1.0, Math.max(0.0, (nowSec - s.startSec) / s.duration));
                                var easeH = 0.5 - 0.5 * Math.cos(localT * Math.PI);
                                curFromHeading = s.startHeading + (easeH * s.headingSweep);
                            } else if (s.type === 'TRANSITION') {
                                var localT = Math.min(1.0, Math.max(0.0, (nowSec - s.startSec) / s.duration));
                                var ease = localT < 0.5 ? 2.0 * localT * localT : -1.0 + (4.0 - 2.0 * localT) * localT;
                                curFromCenter = Cesium.Cartesian3.lerp(s.fromPos, s.toPos, ease, new Cesium.Cartesian3());
                                curFromDist = s.fromRange + (s.toRange - s.fromRange) * ease;
                                curFromPitch = s.fromPitch + (s.toPitch - s.fromPitch) * ease;
                                curFromHeading = s.fromHeading + (s.toHeading - s.fromHeading) * ease;
                            }
                            break;
                        }
                    }

                    // Replace stages with immediate transition to centroid and cluster orbit
                    pinStages = [
                        {
                            type: 'TRANSITION',
                            fromPos: curFromCenter,
                            toPos: targetCartesian,
                            fromRange: curFromDist,
                            toRange: clusterDist,
                            fromPitch: curFromPitch,
                            toPitch: pitchCluster,
                            fromHeading: curFromHeading,
                            toHeading: curFromHeading + (Math.PI * 0.1),
                            startSec: nowSec,
                            endSec: nowSec + transDur,
                            duration: transDur,
                            targetDesc: 'ZOOM_TO_CENTROID'
                        },
                        {
                            type: 'CLUSTER_ORBIT',
                            center: targetCartesian,
                            dist: clusterDist,
                            pitch: pitchCluster,
                            startHeading: curFromHeading + (Math.PI * 0.1),
                            headingSweep: Math.PI * 0.9,
                            startSec: nowSec + transDur,
                            endSec: nowSec + transDur + clusterRemainDur,
                            duration: clusterRemainDur,
                            detonated: true
                        }
                    ];

                    totalSequenceDuration = nowSec + transDur + clusterRemainDur;
                    durationMs = totalSequenceDuration * 1000.0;
                };

                // Start recording chunks
                recorder.start(100);

                function updateRecHUD(curSec, totSec, progress) {
                    var pText = document.getElementById('recProgressText');
                    var pBar = document.getElementById('recProgressBar');
                    if (pText) {
                        var cMin = String(Math.floor(curSec / 60)).padStart(2, '0');
                        var cS = String(curSec % 60).padStart(2, '0');
                        var tMin = String(Math.floor(totSec / 60)).padStart(2, '0');
                        var tS = String(totSec % 60).padStart(2, '0');
                        pText.textContent = cMin + ':' + cS + ' / ' + tMin + ':' + tS;
                    }
                    if (pBar) {
                        pBar.style.width = Math.min(100, Math.round(progress * 100)) + '%';
                    }
                }

                // 9. Frame-by-Frame Continuous Cinematic Director Loop
                var startTime = performance.now();

                function orbitStep(now) {
                    if (!window._isRecordingVideo) return;

                    var elapsed = now - startTime;
                    var elapsedSec = elapsed / 1000.0;
                    var progress = Math.min(1.0, elapsedSec / totalSequenceDuration);

                    // Find current active stage
                    var currentStage = null;
                    for (var si = 0; si < pinStages.length; si++) {
                        var s = pinStages[si];
                        if (elapsedSec >= s.startSec && (elapsedSec < s.endSec || si === pinStages.length - 1)) {
                            currentStage = s;
                            break;
                        }
                    }
                    if (!currentStage) currentStage = pinStages[pinStages.length - 1];

                    var localT = Math.min(1.0, Math.max(0.0, (elapsedSec - currentStage.startSec) / currentStage.duration));
                    var curCenter, curHeading, curPitch, curDist;

                    if (currentStage.type === 'CLUSTER_ORBIT') {
                        // Smooth cosine easing for calm, steady rotation around centroid
                        var easeH = 0.5 - 0.5 * Math.cos(localT * Math.PI);
                        curCenter = currentStage.center;
                        curDist = currentStage.dist;
                        curPitch = currentStage.pitch;
                        curHeading = currentStage.startHeading + (easeH * currentStage.headingSweep);

                        // All blast rings and domes of ALL pins remain visible throughout cluster orbit when anim is not actively overriding
                        if (!currentAnimController) {
                            ensureAllPinZonesVisible();
                        }

                        updateInfoCardForStage(currentStage);

                    } else if (currentStage.type === 'PIN_ORBIT') {
                        // Smooth cosine easing for gentle, calm arc rotation (no whipping/dizziness)
                        var easeH = 0.5 - 0.5 * Math.cos(localT * Math.PI);
                        curCenter = currentStage.center;
                        curDist = currentStage.dist;
                        curPitch = currentStage.pitch;
                        curHeading = currentStage.startHeading + (easeH * currentStage.headingSweep);

                        // Detonate this pin at 0.4s into orbit
                        if (!currentStage.detonated && localT >= (0.4 / currentStage.duration)) {
                            currentStage.detonated = true;
                            detonateSinglePin(currentStage.pinIdx);
                        }

                        // Ensure all PREVIOUSLY detonated pins maintain their blast rings 100% visible
                        for (var pj = 0; pj < currentStage.pinIdx; pj++) {
                            setPinEntitiesVisibility(pinRegistry[pj], true);
                        }

                        updateInfoCardForStage(currentStage);

                    } else if (currentStage.type === 'TRANSITION') {
                        // Smooth Hermite / Quad In-Out ease for smooth flight between targets
                        var ease = localT < 0.5 ? 2.0 * localT * localT : -1.0 + (4.0 - 2.0 * localT) * localT;
                        curCenter = Cesium.Cartesian3.lerp(currentStage.fromPos, currentStage.toPos, ease, new Cesium.Cartesian3());
                        curDist = currentStage.fromRange + (currentStage.toRange - currentStage.fromRange) * ease;
                        curPitch = currentStage.fromPitch + (currentStage.toPitch - currentStage.fromPitch) * ease;
                        curHeading = currentStage.fromHeading + (currentStage.toHeading - currentStage.fromHeading) * ease;

                        if (currentStage.targetDesc === 'ZOOM_TO_OVERVIEW' || currentStage.targetDesc === 'ZOOM_TO_CENTROID') {
                            ensureAllPinZonesVisible();
                        }

                        updateInfoCardForStage(currentStage);

                    } else if (currentStage.type === 'OVERVIEW_ORBIT') {
                        // Smooth cosine easing for steady, slow tactical panorama
                        var easeH = 0.5 - 0.5 * Math.cos(localT * Math.PI);
                        curCenter = currentStage.center;
                        curDist = currentStage.dist;
                        curPitch = currentStage.pitch;
                        curHeading = currentStage.startHeading + (easeH * currentStage.headingSweep);

                        // ALL blast rings and domes of ALL pins remain 100% visible throughout overview
                        ensureAllPinZonesVisible();

                        updateInfoCardForStage(currentStage);
                    }

                    viewer.camera.lookAt(curCenter, new Cesium.HeadingPitchRange(curHeading, curPitch, curDist));
                    try { viewer.scene.render(); } catch(e) {}

                    var elapsedSecFloor = Math.floor(elapsedSec);
                    var totalSecCeil = Math.ceil(totalSequenceDuration);
                    updateRecHUD(elapsedSecFloor, totalSecCeil, progress);

                    if (progress < 1.0) {
                        window._videoOrbitFrameId = requestAnimationFrame(orbitStep);
                    } else {
                        window._videoOrbitFrameId = null;

                        if (animLoopTimer) {
                            clearTimeout(animLoopTimer);
                            animLoopTimer = null;
                        }
                        if (currentAnimController && typeof currentAnimController.stop === 'function') {
                            currentAnimController.stop();
                            currentAnimController = null;
                        }

                        // Immediately unlock camera from orbit transform so user can move freely
                        try {
                            var endPos = viewer.camera.positionWC.clone();
                            var endDir = viewer.camera.directionWC.clone();
                            var endUp = viewer.camera.upWC.clone();
                            viewer.camera.lookAtTransform(Cesium.Matrix4.IDENTITY);
                            viewer.camera.setView({
                                destination: endPos,
                                orientation: {
                                    direction: endDir,
                                    up: endUp
                                }
                            });
                        } catch(e) {
                            try { viewer.camera.lookAtTransform(Cesium.Matrix4.IDENTITY); } catch(ex) {}
                        }
                        try {
                            var ssc = viewer.scene.screenSpaceCameraController;
                            ssc.enableInputs = true;
                            ssc.enableRotate = true;
                            ssc.enableTranslate = true;
                            ssc.enableZoom = true;
                            ssc.enableTilt = true;
                            ssc.enableLook = true;
                        } catch(e) {}

                        // Update HUD to show encoding in progress
                        var expBtn = document.getElementById('exportVideoBtn');
                        if (expBtn) {
                            expBtn.innerHTML = '⏳ ENCODING MP4...';
                        }
                        var pText = document.getElementById('recProgressText');
                        if (pText) {
                            pText.textContent = 'ENCODING MP4 VIDEO...';
                        }
                        var pBar = document.getElementById('recProgressBar');
                        if (pBar) {
                            pBar.style.width = '100%';
                        }

                        if (recorder && recorder.state !== 'inactive') {
                            recorder.stop();
                        }
                    }
                }

                window._videoOrbitFrameId = requestAnimationFrame(orbitStep);
                reportStatus('LOG', '🎥 Started multi-point cinematic sequence (' + Math.round(totalSequenceDuration) + 's total, ' + totalPins + ' strike points)...');
            };

            window.addPin = function(lat, lon, wName, rRed, rOrange, rYellow, alt) {
                lat = parseFloat(lat);
                lon = parseFloat(lon);
                if (isNaN(lat) || isNaN(lon)) return;
                rRed = (rRed !== undefined && rRed !== null && !isNaN(Number(rRed))) ? Number(rRed) : tacticalRadiusConfig.rRed;
                rOrange = (rOrange !== undefined && rOrange !== null && !isNaN(Number(rOrange))) ? Number(rOrange) : tacticalRadiusConfig.rOrange;
                rYellow = (rYellow !== undefined && rYellow !== null && !isNaN(Number(rYellow))) ? Number(rYellow) : tacticalRadiusConfig.rYellow;
                wName = wName || tacticalRadiusConfig.label;
                alt = (typeof alt === 'number' && !isNaN(alt)) ? alt : (parseFloat(alt) || 0);

                var groupId = "PIN_" + Date.now();
                var groundPos = Cesium.Cartesian3.fromDegrees(lon, lat, alt);
                var pos = groundPos;
                var pinEntities = [];

                // ฟังก์ชันสร้างโซนรัศมีอาวุธแบบติด Terrain 100% (แผ่นพื้น + เส้นขอบแนบพื้นดิน + โดม 3 มิติ)
                var createRadiusZone = function(r, color, name) {
                    var fillAlpha = (r <= 12) ? 0.35 : ((r <= 30) ? 0.22 : 0.10);
                    // 1. แผ่นวงกลมแนบชิดผิวพื้นทั้ง Terrain และโมเดลถนน 3D (ClassificationType.BOTH)
                    var groundRing = viewer.entities.add({
                        position: groundPos,
                        ellipse: {
                            semiMajorAxis: r,
                            semiMinorAxis: r,
                            material: color.withAlpha(fillAlpha),
                            classificationType: Cesium.ClassificationType.BOTH
                        },
                        show: !animEnabled
                    });
                    groundRing._pinGroupId = groupId;
                    pinEntities.push(groundRing);

                    // 2. เส้นขอบวงรัศมีแนบติดผิว Terrain 100% (Ground-Clamped Polyline Contour คมชัด ไม่ลอย)
                    var strokeWidth = (r <= 12) ? 4.0 : ((r <= 30) ? 3.0 : 2.2);
                    var groundOutline = viewer.entities.add({
                        name: name + ' Contour',
                        polyline: {
                            positions: getCirclePositions(groundPos, r, 72),
                            width: strokeWidth,
                            material: color.withAlpha(0.95),
                            clampToGround: true
                        },
                        show: !animEnabled
                    });
                    groundOutline._pinGroupId = groupId;
                    pinEntities.push(groundOutline);

                    // 3. โดม 3 มิติครอบพื้นที่เป้าหมาย (ทรงโดมมนโปร่งแสงเนียนตา ไม่มีเส้นตารางโครงลอยเคว้ง outline: false)
                    var domeAlpha = (r <= 12) ? 0.20 : ((r <= 30) ? 0.14 : 0.05);
                    var dome = viewer.entities.add({
                        name: name,
                        position: groundPos,
                        ellipsoid: {
                            radii: new Cesium.Cartesian3(r, r, r),
                            material: color.withAlpha(domeAlpha),
                            outline: false
                        },
                        show: !animEnabled && domeEnabled
                    });
                    dome._pinGroupId = groupId;
                    dome._isDome = true;
                    pinEntities.push(dome);

                    return { groundRing: groundRing, groundOutline: groundOutline, dome: dome, radius: r, color: color };
                };

                // เรียงสร้างจากรัศมีใหญ่ไปเล็ก: เหลือง -> ส้ม -> แดง
                var zoneYellow = createRadiusZone(rYellow, Cesium.Color.YELLOW, wName + ' (Yellow ' + formatR(rYellow) + ')');
                var zoneOrange = createRadiusZone(rOrange, Cesium.Color.ORANGE, wName + ' (Orange ' + formatR(rOrange) + ')');
                var zoneRed = createRadiusZone(rRed, Cesium.Color.RED, wName + ' (Red ' + formatR(rRed) + ')');

                // สร้างรูปภาพ Tactical Badge ที่แสดงระยะพร้อมแถบสีสันคมชัดระดับพิกเซล
                var badgeCanvas = createPinBadgeCanvas(wName, rRed, rOrange, rYellow);
                var badgeDataUrl = badgeCanvas.toDataURL();

                // หมุดจุดกึ่งกลางและ Tactical Badge แสดงรัศมีสีสันชัดเจน (ยึดติดผิวดิน CLAMP_TO_GROUND)
                var marker = viewer.entities.add({
                    position: groundPos,
                    point: {
                        pixelSize: 10,
                        color: Cesium.Color.WHITE,
                        outlineColor: Cesium.Color.BLACK,
                        outlineWidth: 2,
                        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
                        disableDepthTestDistance: Number.POSITIVE_INFINITY
                    },
                    billboard: {
                        image: badgeDataUrl,
                        verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
                        pixelOffset: new Cesium.Cartesian2(0, -8),
                        scale: 0.5,
                        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
                        disableDepthTestDistance: Number.POSITIVE_INFINITY
                    },
                    show: !animEnabled
                });
                marker._pinGroupId = groupId;
                pinEntities.push(marker);

                pinRegistry.push({
                    id: groupId,
                    lat: lat,
                    lon: lon,
                    alt: alt,
                    cartesian: groundPos,
                    label: wName,
                    rRed: rRed,
                    rOrange: rOrange,
                    rYellow: rYellow,
                    entities: pinEntities
                });

                if (animEnabled) {
                    playExplosionSound();
                    playExplosionAnimation(pos, groundPos, rRed, rOrange, rYellow, wName, {
                        pinId: groupId,
                        lat: lat,
                        lon: lon,
                        zoneRed: zoneRed,
                        zoneOrange: zoneOrange,
                        zoneYellow: zoneYellow,
                        marker: marker
                    }, function() {
                        if (!animLoop) {
                            var p = pinRegistry.find(function(item) { return item.id === groupId; });
                            if (p) openPinControlBar(p);
                        }
                    });
                } else {
                    var newlyAddedPin = pinRegistry[pinRegistry.length - 1];
                    openPinControlBar(newlyAddedPin);
                }

                reportStatus("LOG", "Dropped Pin: " + Number(lat).toFixed(4) + ", " + Number(lon).toFixed(4) + " [🔴" + formatR(rRed) + " 🟠" + formatR(rOrange) + " 🟡" + formatR(rYellow) + "]");
                selectedPinId = groupId;
                window.selectedPinId = groupId;
                syncDataToQt();
            };

            window.selectedPinId = null;
            var selectedPinId = window.selectedPinId;

            window.selectPin = function(pinId) {
                var p = pinRegistry.find(function(item) { return item.id === pinId; });
                if (p) {
                    selectedPinId = pinId;
                    window.selectedPinId = pinId;
                    openPinControlBar(p);
                } else {
                    selectedPinId = null;
                    window.selectedPinId = null;
                    closePinControlBar();
                }
            };

            function openPinControlBar(pin) {
                closeImageControlBar();
                closeObjectControlBar();
                var guideEl = document.getElementById('drawGuide');
                if (guideEl && !isDrawing) guideEl.style.display = 'none';
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
                if (animLoopTimer) { clearTimeout(animLoopTimer); animLoopTimer = null; }
                if (currentAnimController && typeof currentAnimController.stop === 'function') {
                    currentAnimController.stop();
                    currentAnimController = null;
                }
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
                    
                    if (pinRegistry.length === 0) {
                        repairAllBuildings();
                    }
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
                stopAllAnimations();
                reportStatus("LOG", "Executing Clear All Pins Command...");
                for (var i = 0; i < pinRegistry.length; i++) {
                    var p = pinRegistry[i];
                    for (var j = 0; j < p.entities.length; j++) {
                        viewer.entities.remove(p.entities[j]);
                    }
                }
                window.pinRegistry = [];
                pinRegistry = window.pinRegistry;
                closePinControlBar();
                selectedPinId = null;
                repairAllBuildings();
                reportStatus("LOG", "All Pins, 3D Domes, and Building Damage cleared successfully.");
                syncDataToQt();
            };

            // ▶ LEFT_CLICK — สำหรับวางหมุดเฉพาะเมื่อเปิด Pin Mode (ยึดติดผิวดิน Terrain 100%)
            handler.setInputAction(function(ev) {
                if (pinMode && !editMode) {
                    // หาพิกัดบนผิว Terrain โดยตรง แม้จะคลิกโดนหลังคาตึก เสาอนุสาวรีย์ หรือโมเดล 3D
                    var ray = viewer.camera.getPickRay(ev.position);
                    var groundPos = null;
                    if (ray) {
                        try { groundPos = viewer.scene.globe.pick(ray, viewer.scene); } catch(e) {}
                    }
                    if (!groundPos) {
                        try { groundPos = viewer.camera.pickEllipsoid(ev.position, viewer.scene.globe.ellipsoid); } catch(e) {}
                    }
                    if (!groundPos) {
                        groundPos = pickPos(ev.position);
                    }
                    if (groundPos) {
                        var carto = Cesium.Cartographic.fromCartesian(groundPos);
                        var terrainHeight = 0;
                        try {
                            var h = viewer.scene.globe.getHeight(carto);
                            if (typeof h === 'number' && !isNaN(h)) terrainHeight = h;
                            else if (typeof carto.height === 'number') terrainHeight = carto.height;
                        } catch(e) {
                            terrainHeight = carto.height || 0;
                        }
                        var pinLabel = (document.getElementById('cfgPinLabel') ? document.getElementById('cfgPinLabel').value.trim() : '') || tacticalRadiusConfig.label;
                        addPin(
                            Cesium.Math.toDegrees(carto.latitude),
                            Cesium.Math.toDegrees(carto.longitude),
                            pinLabel,
                            tacticalRadiusConfig.rRed,
                            tacticalRadiusConfig.rOrange,
                            tacticalRadiusConfig.rYellow,
                            terrainHeight
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
                obj.matArr = rgb;
                obj.outArr = [out.red, out.green, out.blue];
                objectRegistry.push(obj);

                refreshPanel();
                selectObj(id);
                reportStatus('LOG', 'Created ' + name + ' (' + Math.round(size) + 'm) at ' + Number(lat).toFixed(4) + ', ' + Number(lon).toFixed(4));
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
                document.getElementById('ocbName').textContent = (SCFG[obj.type] ? SCFG[obj.type].icon : '🏢') + ' ' + (obj._originalState ? obj._originalState.name : obj.name);

                var dmgBadge = document.getElementById('ocbDamageBadge');
                var repBtn = document.getElementById('ocbRepairBtn');
                var dmg = obj.damageLevel || 'INTACT';
                if (dmgBadge && repBtn) {
                    if (dmg === 'DESTROYED') {
                        dmgBadge.style.display = 'inline-block';
                        dmgBadge.textContent = '💥 DESTROYED (100%)';
                        dmgBadge.style.background = 'rgba(255,40,40,0.3)';
                        dmgBadge.style.border = '1px solid #FF4444';
                        dmgBadge.style.color = '#FF8888';
                        repBtn.style.display = 'inline-block';
                    } else if (dmg === 'HEAVILY_DAMAGED') {
                        dmgBadge.style.display = 'inline-block';
                        dmgBadge.textContent = '⚠️ HEAVILY DAMAGED (70%)';
                        dmgBadge.style.background = 'rgba(255,140,0,0.3)';
                        dmgBadge.style.border = '1px solid #FFA500';
                        dmgBadge.style.color = '#FFAA33';
                        repBtn.style.display = 'inline-block';
                    } else if (dmg === 'LIGHT_DAMAGE') {
                        dmgBadge.style.display = 'inline-block';
                        dmgBadge.textContent = '💨 LIGHT DAMAGE (25%)';
                        dmgBadge.style.background = 'rgba(255,230,0,0.2)';
                        dmgBadge.style.border = '1px solid #FFFF44';
                        dmgBadge.style.color = '#FFFF66';
                        repBtn.style.display = 'inline-block';
                    } else {
                        dmgBadge.style.display = 'none';
                        repBtn.style.display = 'none';
                    }
                }

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

            var _syncQtTimer = null;
            function syncDataToQt(immediate) {
                if (immediate) {
                    if (_syncQtTimer) { clearTimeout(_syncQtTimer); _syncQtTimer = null; }
                    _doSyncDataToQt();
                    return;
                }
                if (_syncQtTimer) return;
                _syncQtTimer = setTimeout(function() {
                    _syncQtTimer = null;
                    _doSyncDataToQt();
                }, 120);
            }

            function _doSyncDataToQt() {
                try {
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
                            polyPts: polyPts,
                            damageState: o.damageLevel || 'INTACT',
                            damagePercent: o.damagePercent || 0
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
                    var payload = { objects: objs, images: imgs, pins: pins };
                    window._latestSyncPayload = payload;
                    reportStatus("DATA_SYNC", JSON.stringify(payload));
                } catch(e) {}
            }

            window.getLatestSyncPayloadJson = function() {
                try {
                    return JSON.stringify(window._latestSyncPayload || {});
                } catch(e) {
                    return "{}";
                }
            };

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

            // 💥 Automatic Demonstration Blast on Startup:
            // บินจัดมุมมองกล้องเข้าสู่เป้าหมายที่ใจกลางหน้าจอและจุดระเบิดอัตโนมัติทันที
            setTimeout(function() {
                try {
                    if (window.pinRegistry && window.pinRegistry.length === 0) {
                        var targetCart = Cesium.Cartesian3.fromDegrees(100.5018, 13.7563, 0);
                        viewer.camera.flyToBoundingSphere(new Cesium.BoundingSphere(targetCart, 10), {
                            offset: new Cesium.HeadingPitchRange(0.0, Cesium.Math.toRadians(-35.0), 650.0),
                            duration: 1.0,
                            complete: function() {
                                window.addPin(13.7563, 100.5018, 'MK-82', 9, 15.2, 1219, 0);
                            }
                        });
                    }
                } catch(e) {}
            }, 1200);

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
def render_tactical_hud_card(card_w, card_h, meta):
    try:
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        import cv2

        pins = meta.get('pins', [])
        total_pins = meta.get('totalPins', len(pins))

        card_pil = Image.new('RGB', (card_w, card_h), (15, 23, 42)) # Slate-900
        draw = ImageDraw.Draw(card_pil)

        # Outer border
        draw.rounded_rectangle([0, 0, card_w - 1, card_h - 1], radius=8, outline=(56, 189, 248), width=2)
        # Left accent bar
        draw.rounded_rectangle([0, 0, 6, card_h - 1], radius=2, fill=(56, 189, 248))

        # Fonts
        try:
            font_header = ImageFont.truetype("arialbd.ttf", 15)
            font_sub = ImageFont.truetype("arial.ttf", 11)
            font_item = ImageFont.truetype("arialbd.ttf", 12)
            font_coords = ImageFont.truetype("arial.ttf", 11)
        except Exception:
            font_header = ImageFont.load_default()
            font_sub = ImageFont.load_default()
            font_item = ImageFont.load_default()
            font_coords = ImageFont.load_default()

        cur_y = 12
        # Crosshair icon
        draw.ellipse([16, cur_y + 2, 26, cur_y + 12], outline=(56, 189, 248), width=2)
        draw.line([21, cur_y, 21, cur_y + 14], fill=(56, 189, 248), width=1)
        draw.line([14, cur_y + 7, 28, cur_y + 7], fill=(56, 189, 248), width=1)

        draw.text((34, cur_y), "TACTICAL BLAST ASSESSMENT", font=font_header, fill=(248, 250, 252))
        cur_y += 20
        export_mode = meta.get('exportMode', 'cluster')
        mode_desc = "CLUSTER STRIKE / CENTROID ORBIT" if export_mode == 'cluster' else "SEQUENTIAL TARGET RECON & OVERVIEW"
        draw.text((16, cur_y), f"TOTAL TARGETS: {total_pins}   |   {mode_desc}", font=font_sub, fill=(148, 163, 184))
        cur_y += 18

        # Divider line
        draw.line([16, cur_y, card_w - 16, cur_y], fill=(51, 65, 85), width=1)
        cur_y += 8

        def fmt_m(val):
            try:
                v = float(val)
                if v >= 1000:
                    return f"{v/1000:.1f}km" if (v % 1000) != 0 else f"{int(v//1000)}km"
                return f"{int(round(v))}m"
            except Exception:
                return f"{val}m"

        display_pins = pins[:4]
        for idx, p in enumerate(display_pins):
            lbl = p.get('label', f'POINT #{idx+1}')
            lat = p.get('lat', '0.0000')
            lon = p.get('lon', '0.0000')
            r_red = p.get('rRed', 0)
            r_orange = p.get('rOrange', 0)
            r_yellow = p.get('rYellow', 0)

            draw.text((16, cur_y), f"#{idx+1} {lbl}", font=font_item, fill=(56, 189, 248))
            draw.text((180, cur_y), f"LAT: {lat}°  LON: {lon}°", font=font_coords, fill=(226, 232, 240))
            cur_y += 17

            # Red dot
            draw.ellipse([24, cur_y + 3, 31, cur_y + 10], fill=(239, 68, 68))
            draw.text((35, cur_y), fmt_m(r_red), font=font_coords, fill=(203, 213, 225))

            # Orange dot
            draw.ellipse([90, cur_y + 3, 97, cur_y + 10], fill=(249, 115, 22))
            draw.text((101, cur_y), fmt_m(r_orange), font=font_coords, fill=(203, 213, 225))

            # Yellow dot
            draw.ellipse([160, cur_y + 3, 167, cur_y + 10], fill=(234, 179, 8))
            draw.text((171, cur_y), fmt_m(r_yellow), font=font_coords, fill=(203, 213, 225))

            cur_y += 20

        if len(pins) > 4:
            draw.text((16, cur_y), f"... and {len(pins) - 4} more blast points", font=font_sub, fill=(148, 163, 184))

        return cv2.cvtColor(np.array(card_pil), cv2.COLOR_RGB2BGR)
    except Exception:
        return None

class DiagnosticHTTPHandler(http.server.SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        try:
            content = HTML_MAP_CODE_3D.encode('utf-8')
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content)
        except (ConnectionResetError, BrokenPipeError):
            pass
        except Exception as e:
            try:
                self.send_error(500, f"Server Error: {e}")
            except Exception:
                pass

    def do_HEAD(self):
        try:
            content = HTML_MAP_CODE_3D.encode('utf-8')
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
        except Exception:
            pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Target-Path, X-Pins-Metadata, *")
        self.send_header("Access-Control-Max-Age", "86400")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == '/api/save_video_recording':
                content_len = int(self.headers.get('Content-Length', 0))
                if content_len <= 0:
                    err_json = json.dumps({"status": "error", "error": "Empty video upload (Content-Length is 0)"}).encode('utf-8')
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(err_json)))
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(err_json)
                    return

                # Stream upload chunks directly to disk to prevent RAM bloat or buffer stalls
                temp_webm = tempfile.NamedTemporaryFile(suffix='.webm', delete=False)
                temp_webm_path = temp_webm.name
                bytes_left = content_len
                while bytes_left > 0:
                    chunk = self.rfile.read(min(bytes_left, 65536))
                    if not chunk:
                        break
                    temp_webm.write(chunk)
                    bytes_left -= len(chunk)
                temp_webm.close()

                # Retrieve target path from query string or headers
                qs = urllib.parse.parse_qs(parsed.query)
                target_path = qs.get('path', [''])[0]
                if not target_path:
                    hdr_path = self.headers.get('X-Target-Path', '')
                    if hdr_path:
                        target_path = urllib.parse.unquote(hdr_path)

                if not target_path or target_path == "undefined":
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    target_path = os.path.abspath(f"blast_simulation_{ts}.mp4").replace("\\", "/")
                else:
                    target_path = os.path.abspath(target_path).replace("\\", "/")

                os.makedirs(os.path.dirname(target_path), exist_ok=True)

                # Retrieve pins metadata for tactical HUD overlay
                meta_str = qs.get('meta', [''])[0]
                if not meta_str:
                    hdr_meta = self.headers.get('X-Pins-Metadata', '')
                    if hdr_meta:
                        meta_str = urllib.parse.unquote(hdr_meta)

                pins_meta = {}
                if meta_str:
                    try:
                        pins_meta = json.loads(meta_str)
                    except Exception:
                        pins_meta = {}

                temp_mp4 = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
                temp_mp4_path = temp_mp4.name
                temp_mp4.close()

                success = False
                err_msg = ""
                frames_count = 0

                try:
                    import cv2
                    cap = None
                    try:
                        cap = cv2.VideoCapture(temp_webm_path, cv2.CAP_FFMPEG)
                        if not cap.isOpened():
                            cap = cv2.VideoCapture(temp_webm_path)
                    except Exception:
                        cap = cv2.VideoCapture(temp_webm_path)

                    if not cap or not cap.isOpened():
                        raise RuntimeError(f"Cannot decode recorded video stream ({content_len} bytes)")

                    fps = 30.0
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    if w <= 0 or h <= 0:
                        ret_probe, frame_probe = cap.read()
                        if ret_probe and frame_probe is not None:
                            h, w = frame_probe.shape[:2]
                            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        else:
                            w, h = 1920, 1080

                    # Standardize even dimensions for video encoders
                    w = w - (w % 2)
                    h = h - (h % 2)

                    # Pre-render Tactical Top-Left HUD Card if pins are present
                    hud_card = None
                    hud_x, hud_y = 28, 28
                    card_w, card_h = 470, 0
                    if pins_meta and pins_meta.get('pins'):
                        p_count = min(4, len(pins_meta['pins']))
                        card_h = 76 + (p_count * 40)
                        if len(pins_meta['pins']) > 4:
                            card_h += 24
                        card_w = min(490, max(360, w - 56))
                        hud_card = render_tactical_hud_card(card_w, card_h, pins_meta)

                    # Initialize VideoWriter with universal codecs:
                    # 1. mp4v: Standard ISO MPEG-4 Part 2, built into OpenCV, plays natively in Windows Media Player & all platforms
                    writer = None
                    try:
                        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                        w_cand = cv2.VideoWriter(temp_mp4_path, fourcc, fps, (w, h))
                        if w_cand.isOpened():
                            writer = w_cand
                    except Exception:
                        writer = None

                    # 2. H.264 via MSMF fallback
                    if writer is None or not writer.isOpened():
                        try:
                            fourcc = cv2.VideoWriter_fourcc(*'H264')
                            w_cand = cv2.VideoWriter(temp_mp4_path, cv2.CAP_MSMF, fourcc, fps, (w, h))
                            if w_cand.isOpened():
                                writer = w_cand
                        except Exception:
                            writer = None

                    # 3. avc1 fallback
                    if writer is None or not writer.isOpened():
                        try:
                            fourcc = cv2.VideoWriter_fourcc(*'avc1')
                            w_cand = cv2.VideoWriter(temp_mp4_path, fourcc, fps, (w, h))
                            if w_cand.isOpened():
                                writer = w_cand
                        except Exception:
                            writer = None

                    if writer is None or not writer.isOpened():
                        raise RuntimeError("Failed to initialize MP4 VideoWriter encoder")

                    while True:
                        ret, frame = cap.read()
                        if not ret or frame is None:
                            break
                        if frame.shape[1] != w or frame.shape[0] != h:
                            frame = cv2.resize(frame, (w, h))

                        # Blend top-left tactical HUD card directly onto frame
                        if hud_card is not None and h >= (hud_y + card_h) and w >= (hud_x + card_w):
                            roi = frame[hud_y:hud_y + card_h, hud_x:hud_x + card_w]
                            cv2.addWeighted(roi, 0.15, hud_card, 0.85, 0, roi)

                        writer.write(frame)
                        frames_count += 1

                    writer.release()
                    cap.release()

                    if frames_count > 0 and os.path.exists(temp_mp4_path) and os.path.getsize(temp_mp4_path) > 1024:
                        import shutil
                        shutil.copyfile(temp_mp4_path, target_path)
                        success = True
                    else:
                        raise RuntimeError(f"Video encoding produced 0 frames (frames_count={frames_count})")

                except Exception as ex:
                    err_msg = str(ex)
                    print(f"[VIDEO_EXPORT_ERROR] {err_msg}", file=sys.stderr)
                finally:
                    for p in [temp_webm_path, temp_mp4_path]:
                        try:
                            if os.path.exists(p):
                                os.remove(p)
                        except Exception:
                            pass

                if success and os.path.exists(target_path):
                    f_size = os.path.getsize(target_path)
                    resp_data = json.dumps({
                        "status": "ok",
                        "path": target_path.replace("\\", "/"),
                        "size": f_size
                    }).encode('utf-8')
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(resp_data)))
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(resp_data)
                else:
                    err_json = json.dumps({"status": "error", "error": err_msg or "Failed to encode MP4 video"}).encode('utf-8')
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(err_json)))
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(err_json)
                return
            else:
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
        except Exception as e:
            import traceback
            traceback.print_exc()
            err_json = json.dumps({"status": "error", "error": f"Server POST error: {e}"}).encode('utf-8')
            try:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(err_json)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(err_json)
            except Exception:
                pass

    def log_message(self, format, *args):
        pass

class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

def run_auto_port_server():
    server = ThreadingTCPServer(("127.0.0.1", 0), DiagnosticHTTPHandler)
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
        endpoints = [
            'https://overpass-api.de/api/interpreter',
            'https://overpass.kumi.systems/api/interpreter'
        ]
        data = None
        for ep in endpoints:
            try:
                req = urllib.request.Request(ep, data=query.encode('utf-8'), headers={'User-Agent': 'CesiumCFDExport/1.0'})
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    if data and 'elements' in data:
                        break
            except Exception:
                continue

        if not data:
            return []
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
        y = (float(lat) - lat0) * (math.pi / 180.0) * 6378137.0
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
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("# Wavefront OBJ exported by Cesium 3D Platform\n")
        f.write("# Unit: Meters (Local ENU Cartesian Frame)\n")
        f.write("# Compatible with OpenFOAM snappyHexMesh, Blender, CAD\n\n")

        v_offset = 1
        for grp in groups:
            raw_name = str(grp.get('name', 'solid')).strip()
            clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', raw_name) or 'object'
            f.write(f"o {clean_name}\n")
            triangles = grp.get('triangles', [])
            for tri in triangles:
                for v in tri:
                    f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
            for i in range(len(triangles)):
                idx = v_offset + i * 3
                f.write(f"f {idx} {idx+1} {idx+2}\n")
            v_offset += len(triangles) * 3
            f.write("\n")

def write_stl_file(filepath, groups):
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        for grp in groups:
            raw_name = str(grp.get('name', 'solid')).strip()
            clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', raw_name) or 'solid_mesh'
            f.write(f"solid {clean_name}\n")
            for tri in grp.get('triangles', []):
                norm = compute_face_normal(tri[0], tri[1], tri[2])
                f.write(f"  facet normal {norm[0]:.6e} {norm[1]:.6e} {norm[2]:.6e}\n")
                f.write("    outer loop\n")
                f.write(f"      vertex {tri[0][0]:.4f} {tri[0][1]:.4f} {tri[0][2]:.4f}\n")
                f.write(f"      vertex {tri[1][0]:.4f} {tri[1][1]:.4f} {tri[1][2]:.4f}\n")
                f.write(f"      vertex {tri[2][0]:.4f} {tri[2][1]:.4f} {tri[2][2]:.4f}\n")
                f.write("    endloop\n")
                f.write("  endfacet\n")
            f.write(f"endsolid {clean_name}\n")

class Export3DDialog(QDialog):
    def __init__(self, parent, objects):
        super().__init__(parent)
        self.setWindowTitle("📤 Export 3D Models (.OBJ / .STL) for OpenFOAM & CAD")
        self.resize(560, 520)
        self.objects = objects

        self.setStyleSheet("""
            QDialog { background-color: #0F172A; color: #F8FAFC; font-family: 'Segoe UI', 'Consolas', sans-serif; }
            QLabel { color: #E2E8F0; font-size: 11px; }
            QGroupBox {
                border: 1px solid #334155; border-radius: 6px; margin-top: 12px;
                font-weight: bold; color: #38BDF8; padding-top: 14px; font-size: 12px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
            QPushButton {
                background-color: #2563EB; color: #FFF; border: 1px solid #3B82F6;
                border-radius: 4px; padding: 6px 12px; font-weight: bold; font-family: 'Segoe UI', 'Consolas', sans-serif;
            }
            QPushButton:hover { background-color: #1D4ED8; border-color: #60A5FA; }
            QListWidget {
                background-color: #020617; border: 1px solid #334155; border-radius: 4px;
                color: #F8FAFC; font-family: 'Consolas', monospace; font-size: 11px;
            }
            QListWidget::item { padding: 4px 6px; }
            QListWidget::item:hover { background-color: #1E293B; }
            QRadioButton, QCheckBox { color: #E2E8F0; font-size: 11px; }
            QSpinBox {
                background-color: #1E293B; color: #FFF; border: 1px solid #334155;
                padding: 4px 8px; border-radius: 4px; font-family: 'Consolas', monospace;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header Info Banner
        info_banner = QLabel("📐 <b>Metric ENU Coordinates (Meters) centered at (0, 0, 0)</b><br>"
                             "<font color='#38BDF8'>Preserves real-world distances between objects for OpenFOAM CFD, Blender, and CAD.</font>")
        info_banner.setStyleSheet("background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; padding: 8px; border-radius: 4px;")
        layout.addWidget(info_banner)

        # 1. Object Selection List
        obj_grp = QGroupBox("1. Select 3D Models to Export:")
        obj_layout = QVBoxLayout(obj_grp)
        obj_layout.setSpacing(6)

        sel_btn_row = QHBoxLayout()
        sel_all_b = QPushButton("Select All")
        sel_all_b.setStyleSheet("background: #1E293B; border: 1px solid #334155; color: #E2E8F0; padding: 3px 8px; font-size: 10px;")
        sel_all_b.clicked.connect(self.select_all_objects)
        sel_btn_row.addWidget(sel_all_b)

        desel_all_b = QPushButton("Deselect All")
        desel_all_b.setStyleSheet("background: #7F1D1D; border: 1px solid #991B1B; color: #FECACA; padding: 3px 8px; font-size: 10px;")
        desel_all_b.clicked.connect(self.deselect_all_objects)
        sel_btn_row.addWidget(desel_all_b)
        sel_btn_row.addStretch()
        obj_layout.addLayout(sel_btn_row)

        self.obj_checklist = QListWidget()
        self.item_checkboxes = []
        if self.objects:
            for obj in self.objects:
                item = QListWidgetItem()
                cb = QCheckBox(f"{obj.get('name', 'Object')} ({str(obj.get('type', 'box')).upper()}) - Height: {obj.get('height', 20)}m")
                cb.setChecked(True)
                self.obj_checklist.addItem(item)
                self.obj_checklist.setItemWidget(item, cb)
                self.item_checkboxes.append((cb, obj))
        else:
            item = QListWidgetItem()
            note = QLabel("<font color='#FFAA33'>ℹ️ No custom 3D objects yet. You can export surrounding Cesium OSM Buildings below.</font>")
            self.obj_checklist.addItem(item)
            self.obj_checklist.setItemWidget(item, note)
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
        export_b.setStyleSheet("background: #2563EB; color: #FFFFFF; font-weight: bold; padding: 7px 18px; border: 1px solid #3B82F6;")
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
        include_osm = self.cesium_osm_cb.isChecked()
        if not selected and not include_osm:
            QMessageBox.warning(self, "No Selection", "Please select at least one 3D object or enable Cesium OSM Buildings to export.")
            return

        fmt_id = self.fmt_group.checkedId()
        if fmt_id not in (1, 2, 3):
            fmt_id = 3

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

        # Determine center coordinate safely
        osm_buildings = []
        if include_osm:
            if selected:
                c_lat = sum(float(o.get('lat', 0.0)) for o in selected) / len(selected)
                c_lon = sum(float(o.get('lon', 0.0)) for o in selected) / len(selected)
                c_th = min(float(o.get('th', 0.0)) for o in selected)
            elif hasattr(self.parent(), 'current_pins_raw') and self.parent().current_pins_raw:
                p = self.parent().current_pins_raw[-1]
                c_lat = float(p.get('lat', 13.7563))
                c_lon = float(p.get('lon', 100.5018))
                c_th = float(p.get('alt', 0.0))
            else:
                c_lat, c_lon, c_th = 13.7563, 100.5018, 0.0

            r_meters = float(self.osm_radius_spin.value())
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                osm_buildings = fetch_surrounding_osm_buildings(c_lat, c_lon, r_meters, center_th=c_th)
            finally:
                QApplication.restoreOverrideCursor()

        all_to_export = selected + osm_buildings
        if not all_to_export:
            QMessageBox.warning(self, "No 3D Models Found", "No 3D objects or OSM buildings were found in the selected area to export.")
            return

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

            if not saved_files:
                QMessageBox.warning(self, "Export Notice", "No output files were written. Please verify the selected format.")
                return

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
        self.setWindowTitle("💥 CESIUM 3D EXPLOSION RADIUS & WEAPON EFFECT SIMULATOR (was_test7)")
        self.resize(1400, 900)
        self.target_port = target_port
        self.edit_mode = False

        self.setStyleSheet("""
            QWidget { background-color: #0F172A; color: #E2E8F0; font-family: 'Segoe UI', 'Consolas', sans-serif; }
            QLineEdit {
                background-color: #1E293B; border: 1px solid #334155; color: #F8FAFC;
                padding: 5px 8px; font-family: 'Consolas', monospace; font-size: 12px; border-radius: 4px;
            }
            QLineEdit:focus { border-color: #3B82F6; }
            QComboBox {
                background-color: #1E293B; border: 1px solid #334155; color: #F8FAFC;
                padding: 5px 8px; font-family: 'Consolas', monospace; font-size: 12px; border-radius: 4px;
            }
            QComboBox QAbstractItemView { background-color: #0F172A; color: #F8FAFC; selection-background-color: #2563EB; }
            QPushButton {
                background-color: #2563EB; color: #FFFFFF; border: 1px solid #3B82F6; font-weight: bold;
                padding: 6px 12px; border-radius: 4px; font-family: 'Segoe UI', 'Consolas', sans-serif;
            }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton:checked { background-color: #1D4ED8; color: #FFFFFF; }
            QTextEdit { background-color: #020617; border: 1px solid #334155; color: #CBD5E1; font-size: 12px; }
            QLabel { font-weight: bold; color: #F8FAFC; font-size: 12.5px; }
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
        self.web_view.renderProcessTerminated.connect(self.on_render_process_terminated)
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
        
        # Header Row with Title and Actions
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.addWidget(QLabel("📋 OBJECT & OVERLAY DATA:"))
        header_row.addStretch()

        export_video_b = QPushButton("🎥 EXPORT MP4")
        export_video_b.setStyleSheet("background: #4F46E5; color: #FFF; font-size: 10px; font-weight: bold; padding: 4px 11px; border-radius: 3px; border: 1px solid #6366F1;")
        export_video_b.setToolTip("บันทึกวิดีโอวงโคจร 360° รอบจุดระเบิด (Export 360° Orbit Blast Simulation Video)")
        export_video_b.clicked.connect(self.prompt_video_save_path)
        header_row.addWidget(export_video_b)

        repair_all_b = QPushButton("🔨 REPAIR ALL")
        repair_all_b.setStyleSheet("background: #0284C7; color: #FFF; font-size: 10px; font-weight: bold; padding: 4px 11px; border-radius: 3px; border: 1px solid #38BDF8;")
        repair_all_b.setToolTip("Restore all 3D buildings back to 100% pristine condition")
        repair_all_b.clicked.connect(self.repair_all_buildings_qt)
        header_row.addWidget(repair_all_b)
        panel_layout.addLayout(header_row)

        self.data_tabs = QTabWidget()
        self.data_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #334155; background: #0F172A; }
            QTabBar::tab { background: #1E293B; color: #94A3B8; padding: 6px 14px; font-weight: bold; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
            QTabBar::tab:selected { background: #2563EB; color: #FFFFFF; }
        """)

        # Tab 1: 3D Objects
        self.obj_list_widget = QListWidget()
        self.obj_list_widget.setStyleSheet("background: #020617; border: none; color: #E2E8F0;")
        self.data_tabs.addTab(self.obj_list_widget, "🏢 Objects (0)")

        # Tab 2: Image Overlays
        self.img_list_widget = QListWidget()
        self.img_list_widget.setStyleSheet("background: #020617; border: none; color: #E2E8F0;")
        self.data_tabs.addTab(self.img_list_widget, "🖼️ Images (0)")

        # Tab 3: Tactical Pins
        self.pin_list_widget = QListWidget()
        self.pin_list_widget.setStyleSheet("background: #020617; border: none; color: #E2E8F0;")
        self.data_tabs.addTab(self.pin_list_widget, "🎯 Pins (0)")

        panel_layout.addWidget(self.data_tabs)
        bottom_layout.addWidget(panel_box, 5)

        # 🔽 / 🔼 Collapse/Expand Toggle Bar for Bottom Panel
        toggle_bar = QHBoxLayout()
        toggle_bar.setContentsMargins(0, 0, 0, 0)
        toggle_bar.setSpacing(6)

        sep_left = QFrame()
        sep_left.setFrameShape(QFrame.HLine)
        sep_left.setStyleSheet("border: none; border-top: 1px solid #334155;")

        self.toggle_bottom_btn = QPushButton("▼ HIDE PANEL (กดเพื่อซ่อนแผงด้านล่าง)")
        self.toggle_bottom_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_bottom_btn.setToolTip("คลิกเพื่อ ยุบ/ขยาย แผงบันทึกข้อความและข้อมูลวัตถุ (กด F12 เพื่อสลับได้)")
        self.toggle_bottom_btn.setShortcut("F12")
        self.toggle_bottom_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E293B; color: #94A3B8;
                border: 1px solid #334155; border-radius: 4px;
                padding: 4px 18px; font-weight: bold; font-size: 11px;
                font-family: 'Segoe UI', 'Consolas', sans-serif;
            }
            QPushButton:hover {
                background-color: #2563EB; color: #FFFFFF;
                border-color: #3B82F6;
            }
        """)
        self.toggle_bottom_btn.clicked.connect(self.toggle_bottom_panel)

        sep_right = QFrame()
        sep_right.setFrameShape(QFrame.HLine)
        sep_right.setStyleSheet("border: none; border-top: 1px solid #334155;")

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
                    background-color: #1E293B; color: #38BDF8;
                    border: 1px solid #3B82F6; border-radius: 4px;
                    padding: 4px 18px; font-weight: bold; font-size: 11px;
                    font-family: 'Segoe UI', 'Consolas', sans-serif;
                }
                QPushButton:hover {
                    background-color: #2563EB; color: #FFFFFF;
                }
            """)
            self.main_layout.setStretch(1, 1)
        else:
            self.bottom_container.show()
            self.toggle_bottom_btn.setText("▼ HIDE PANEL (กดเพื่อซ่อนแผงด้านล่าง)")
            self.toggle_bottom_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1E293B; color: #94A3B8;
                    border: 1px solid #334155; border-radius: 4px;
                    padding: 4px 18px; font-weight: bold; font-size: 11px;
                    font-family: 'Segoe UI', 'Consolas', sans-serif;
                }
                QPushButton:hover {
                    background-color: #2563EB; color: #FFFFFF;
                    border-color: #3B82F6;
                }
            """)
            self.main_layout.setStretch(1, 7)
            self.main_layout.setStretch(3, 3)

    def on_render_process_terminated(self, termination_status, exit_code):
        try:
            self.debug_log.append(f"⚠️ <font color='#FFAA33'>WebGL rendering process recovered (status={termination_status}, code={exit_code}). Restoring viewport...</font>")
            self.web_view.reload()
        except Exception:
            pass

    def capture_js_logs(self, title):
        try:
            if not title or "|" not in title:
                return
            parts = title.split("|", 2)
            if len(parts) == 3:
                prefix, seq, msg = parts
            elif len(parts) == 2:
                prefix, msg = parts
            else:
                return

            if prefix == "LOG":
                self.debug_log.append(f"🟢 {msg}")
            elif prefix == "SUCCESS":
                self.debug_log.append(f"⭐ <font color='#4ADE80'>{msg}</font>")
            elif prefix == "ERROR":
                self.debug_log.append(f"🚨 <font color='#EF4444'>{msg}</font>")
            elif prefix == "EXPORT_3D_TRIGGER":
                self.open_export_dialog()
            elif prefix == "REQUEST_VIDEO_PATH":
                self.prompt_video_save_path(msg)
            elif prefix == "VIDEO_SAVED":
                self.show_video_saved_dialog(msg)
            elif prefix == "DATA_SYNC":
                try:
                    payload = json.loads(msg)
                    self.update_qt_data_panel(payload)
                except Exception:
                    # In case of Chromium title truncation, request untruncated payload directly from JS
                    self.web_view.page().runJavaScript(
                        "window.getLatestSyncPayloadJson ? window.getLatestSyncPayloadJson() : JSON.stringify(window._latestSyncPayload || {})",
                        self.on_full_sync_data_received
                    )
        except Exception as e:
            self.debug_log.append(f"⚠️ IPC handler exception: {e}")

    def prompt_video_save_path(self, mode="cluster"):
        try:
            if not isinstance(mode, str) or not mode or mode in ("mp4", "False"):
                mode = "cluster"
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_path = os.path.abspath(f"blast_orbit_simulation_{ts}.mp4").replace("\\", "/")
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "🎥 Export 360° Blast Simulation Video",
                default_path,
                "MP4 Video Files (*.mp4)"
            )
            if save_path:
                if not save_path.lower().endswith(".mp4"):
                    save_path += ".mp4"
                save_path = os.path.abspath(save_path).replace("\\", "/")
                self.debug_log.append(f"🎥 <font color='#38BDF8'>Starting 360° video recording ({mode} mode) to: {save_path}</font>")
                self.web_view.page().runJavaScript(f"startVideoRecording({json.dumps(save_path)}, 20.0, {json.dumps(mode)});")
        except Exception as e:
            self.debug_log.append(f"🚨 Failed to prompt save path: {e}")

    def show_video_saved_dialog(self, json_msg):
        try:
            data = json.loads(json_msg) if json_msg else {}
            video_path = data.get("path", "")
            f_size = data.get("size", 0)
            size_mb = f_size / (1024 * 1024) if f_size > 0 else 0.0

            dlg = QDialog(self)
            dlg.setWindowTitle("🎥 360° Video Export Complete")
            dlg.resize(500, 240)
            dlg.setStyleSheet("""
                QDialog { background-color: #0F172A; color: #F8FAFC; font-family: 'Segoe UI', 'Consolas', sans-serif; }
                QLabel { color: #E2E8F0; font-size: 12px; }
                QPushButton {
                    background-color: #2563EB; color: #FFFFFF; font-weight: bold;
                    border: 1px solid #3B82F6; border-radius: 4px; padding: 7px 16px; font-size: 11px;
                }
                QPushButton:hover { background-color: #1D4ED8; }
            """)
            d_layout = QVBoxLayout(dlg)
            d_layout.setContentsMargins(18, 18, 18, 18)
            d_layout.setSpacing(12)

            header = QLabel("✅ <b>บันทึกวิดีโอ 360° MP4 สำเร็จเรียบร้อยแล้ว!</b>")
            header.setStyleSheet("color: #38BDF8; font-size: 14px;")
            d_layout.addWidget(header)

            info = QLabel(
                f"<b>📍 ตำแหน่งไฟล์:</b><br><font color='#94A3B8'>{video_path}</font><br><br>"
                f"<b>📊 ขนาดไฟล์:</b> {size_mb:.2f} MB ({f_size:,} bytes)<br>"
                f"<b>⏱️ รูปแบบ:</b> 360° Orbit Loop Animation • 30 FPS • MP4 Video"
            )
            info.setWordWrap(True)
            d_layout.addWidget(info)

            btn_box = QHBoxLayout()
            btn_box.setSpacing(10)

            play_btn = QPushButton("▶️ Open Video (เปิดดูวิดีโอ)")
            def on_play():
                try:
                    norm = os.path.normpath(video_path)
                    if os.path.exists(norm):
                        os.startfile(norm)
                except Exception as ex:
                    QMessageBox.warning(dlg, "Error", f"Cannot open video: {ex}")
            play_btn.clicked.connect(on_play)
            btn_box.addWidget(play_btn)

            folder_btn = QPushButton("📁 Open Folder (เปิดโฟลเดอร์)")
            def on_folder():
                try:
                    norm = os.path.normpath(video_path)
                    import subprocess
                    subprocess.Popen(['explorer', f'/select,{norm}'])
                except Exception:
                    pass
            folder_btn.clicked.connect(on_folder)
            btn_box.addWidget(folder_btn)

            close_btn = QPushButton("Close")
            close_btn.setStyleSheet("background-color: #334155; border-color: #475569; color: #CBD5E1;")
            close_btn.clicked.connect(dlg.accept)
            btn_box.addWidget(close_btn)

            d_layout.addLayout(btn_box)
            dlg.exec()
        except Exception as e:
            self.debug_log.append(f"🚨 Dialog display error: {e}")

    def on_full_sync_data_received(self, json_str):
        try:
            if json_str and json_str != "{}":
                payload = json.loads(json_str)
                self.update_qt_data_panel(payload)
        except Exception as e:
            self.debug_log.append(f"⚠️ Full sync parse exception: {e}")

    def open_export_dialog(self):
        try:
            objs = getattr(self, 'current_objects_raw', []) or []
            dlg = Export3DDialog(self, objs)
            dlg.exec()
        except Exception as e:
            self.debug_log.append(f"🚨 Failed to open export dialog: {e}")

    def repair_all_buildings_qt(self):
        try:
            self.web_view.page().runJavaScript("repairAllBuildings();")
        except Exception:
            pass

    def pick_object_color_qt(self, obj_id, cur_hex):
        try:
            color = QColorDialog.getColor(initial=QColor(cur_hex), parent=self, title="Pick Object Color")
            if color.isValid():
                hex_val = color.name()
                self.web_view.page().runJavaScript(f"modifyObjColor({obj_id}, '{hex_val}');")
        except Exception:
            pass

    def update_qt_data_panel(self, data):
        try:
            # 1. Immediate exit if payload has not changed to eliminate unnecessary repaints
            payload_json = json.dumps(data, sort_keys=True)
            if getattr(self, '_last_qt_payload_hash', None) == payload_json:
                return
            self._last_qt_payload_hash = payload_json

            objects = data.get("objects", [])
            images = data.get("images", [])
            pins = data.get("pins", [])
            self.current_objects_raw = objects
            self.current_images_raw = images
            self.current_pins_raw = pins

            # Freeze visual updates on data_tabs during list rebuilds to eliminate tab bar flashing/flickering
            self.data_tabs.setUpdatesEnabled(False)
            self.obj_list_widget.blockSignals(True)
            self.img_list_widget.blockSignals(True)
            self.pin_list_widget.blockSignals(True)

            # Update Tab 1: 3D Objects only if objects data actually changed
            obj_json = json.dumps(objects, sort_keys=True)
            if getattr(self, '_last_obj_hash', None) != obj_json:
                self._last_obj_hash = obj_json
                t0_text = f"🏢 Objects ({len(objects)})"
                if self.data_tabs.tabText(0) != t0_text:
                    self.data_tabs.setTabText(0, t0_text)
                self.obj_list_widget.clear()
                for o in objects:
                    item = QListWidgetItem()
                    w = QWidget()
                    row = QHBoxLayout(w)
                    row.setContentsMargins(6, 2, 6, 2)
                    row.setSpacing(5)

                    sz_val = o.get('width', o.get('size', 50))
                    color_hex = o.get('colorHex', '#00E5FF')
                    dmg_state = o.get('damageState', 'INTACT')
                    if dmg_state == 'DESTROYED':
                        badge_html = " <span style='background:#7F1D1D; color:#FCA5A5; padding:1px 5px; border-radius:3px; font-size:9px; font-weight:bold;'>💥 DESTROYED (100%)</span>"
                    elif dmg_state == 'HEAVILY_DAMAGED':
                        badge_html = " <span style='background:#78350F; color:#FDBA74; padding:1px 5px; border-radius:3px; font-size:9px; font-weight:bold;'>⚠️ HEAVY (70%)</span>"
                    elif dmg_state == 'LIGHT_DAMAGE':
                        badge_html = " <span style='background:#713F12; color:#FDE047; padding:1px 5px; border-radius:3px; font-size:9px; font-weight:bold;'>💨 LIGHT (25%)</span>"
                    else:
                        badge_html = ""
                    o_name_clean = html.escape(str(o.get('name', 'Object')))
                    o_type_clean = html.escape(str(o.get('type', 'box')).upper())
                    o_height_val = o.get('height', 20)
                    info_text = f"<span style='color:{color_hex}; font-size:13px;'>●</span> <b>{o_name_clean}</b> ({o_type_clean}) H:{o_height_val}m Sz:{sz_val}m{badge_html}"
                    info = QLabel(info_text)
                    info.setStyleSheet("color: #F8FAFC; font-size: 11px;")
                    row.addWidget(info, 1)

                    oid = o.get('id', 0)

                    # Repair single building button if damaged
                    if dmg_state != 'INTACT':
                        rep_b = QPushButton("🔨")
                        rep_b.setStyleSheet("background: #0284C7; color: #FFF; font-size: 10px; padding: 2px 6px; font-weight: bold; border-radius: 3px;")
                        rep_b.setToolTip("Repair this building back to 100% pristine condition")
                        rep_b.clicked.connect(lambda checked, i=oid: self.web_view.page().runJavaScript(f"repairSingleBuilding({i});"))
                        row.addWidget(rep_b)

                    # Color Picker Button
                    clr_b = QPushButton("🎨")
                    clr_b.setStyleSheet(f"background: {color_hex}; color: #000; font-size: 10px; padding: 2px 6px; font-weight: bold; border: 1px solid #FFF; border-radius: 3px;")
                    clr_b.setToolTip("Change object color")
                    clr_b.clicked.connect(lambda checked, i=oid, cur=color_hex: self.pick_object_color_qt(i, cur))
                    row.addWidget(clr_b)

                    # Height +/- and direct input
                    hin_b = QPushButton("+H")
                    hin_b.setStyleSheet("background: #1E293B; color: #38BDF8; border: 1px solid #475569; font-size: 10px; padding: 2px 5px; font-weight: bold; border-radius: 3px;")
                    hin_b.clicked.connect(lambda checked, i=oid: self.web_view.page().runJavaScript(f"modifyObjDimensions({i}, 1.0, 5);"))
                    row.addWidget(hin_b)

                    hout_b = QPushButton("-H")
                    hout_b.setStyleSheet("background: #1E293B; color: #38BDF8; border: 1px solid #475569; font-size: 10px; padding: 2px 5px; font-weight: bold; border-radius: 3px;")
                    hout_b.clicked.connect(lambda checked, i=oid: self.web_view.page().runJavaScript(f"modifyObjDimensions({i}, 1.0, -5);"))
                    row.addWidget(hout_b)

                    h_spin = QSpinBox()
                    h_spin.setRange(1, 10000)
                    try:
                        h_val = int(float(o.get('height') or 20))
                    except Exception:
                        h_val = 20
                    h_spin.setValue(h_val)
                    h_spin.setSuffix("m")
                    h_spin.setToolTip("Directly edit height in meters")
                    h_spin.setStyleSheet("background: #1E293B; color: #F8FAFC; border: 1px solid #334155; font-size: 10px; padding: 1px 2px; border-radius: 3px;")
                    h_spin.setFixedWidth(58)

                    def make_height_setter(spin_widget, object_id):
                        def on_change():
                            try:
                                if spin_widget:
                                    self.web_view.page().runJavaScript(f"setObjHeight({object_id}, {spin_widget.value()});")
                            except Exception:
                                pass
                        return on_change

                    h_spin.editingFinished.connect(make_height_setter(h_spin, oid))
                    row.addWidget(h_spin)

                    # Size +/-
                    szin_b = QPushButton("+Sz")
                    szin_b.setStyleSheet("background: #1E293B; color: #38BDF8; border: 1px solid #475569; font-size: 10px; padding: 2px 5px; font-weight: bold; border-radius: 3px;")
                    szin_b.clicked.connect(lambda checked, i=oid: self.web_view.page().runJavaScript(f"modifyObjDimensions({i}, 1.15, 0);"))
                    row.addWidget(szin_b)

                    szout_b = QPushButton("-Sz")
                    szout_b.setStyleSheet("background: #1E293B; color: #38BDF8; border: 1px solid #475569; font-size: 10px; padding: 2px 5px; font-weight: bold; border-radius: 3px;")
                    szout_b.clicked.connect(lambda checked, i=oid: self.web_view.page().runJavaScript(f"modifyObjDimensions({i}, 0.85, 0);"))
                    row.addWidget(szout_b)

                    fly_b = QPushButton("🎯 Fly")
                    fly_b.setStyleSheet("background: #2563EB; color: #FFF; font-size: 10px; padding: 3px 8px; border-radius: 3px;")
                    fly_b.clicked.connect(lambda checked, i=oid: self.web_view.page().runJavaScript(f"selectObj({i});"))
                    row.addWidget(fly_b)

                    del_b = QPushButton("🗑️ Del")
                    del_b.setStyleSheet("background: #7F1D1D; color: #FECACA; font-size: 10px; padding: 3px 8px; border-radius: 3px;")
                    del_b.clicked.connect(lambda checked, i=oid: self.web_view.page().runJavaScript(f"delObj({i});"))
                    row.addWidget(del_b)

                    item.setSizeHint(QSize(420, 36))
                    self.obj_list_widget.addItem(item)
                    self.obj_list_widget.setItemWidget(item, w)

            # Update Tab 2: Image Overlays only if images data actually changed
            img_json = json.dumps(images, sort_keys=True)
            if getattr(self, '_last_img_hash', None) != img_json:
                self._last_img_hash = img_json
                t1_text = f"🖼️ Images ({len(images)})"
                if self.data_tabs.tabText(1) != t1_text:
                    self.data_tabs.setTabText(1, t1_text)
                self.img_list_widget.clear()
                for img in images:
                    item = QListWidgetItem()
                    w = QWidget()
                    row = QHBoxLayout(w)
                    row.setContentsMargins(6, 2, 6, 2)
                    row.setSpacing(6)

                    img_name_clean = html.escape(str(img.get('name', 'Image')))
                    img_scale_str = str(img.get('scale', 1.0))
                    img_rot_str = str(img.get('rotation', 0))
                    img_lat_str = str(img.get('lat', 0))
                    img_lon_str = str(img.get('lon', 0))
                    info_text = f"<b>{img_name_clean}</b> | {img_scale_str}x | {img_rot_str}° | 📍{img_lat_str},{img_lon_str}"
                    info = QLabel(info_text)
                    info.setStyleSheet("color: #38BDF8; font-size: 11px;")
                    row.addWidget(info, 1)

                    iid = img.get('id', 0)
                    rot_left_b = QPushButton("↶ 15°")
                    rot_left_b.setStyleSheet("background: #1E293B; color: #38BDF8; border: 1px solid #475569; font-size: 10px; padding: 3px 5px; border-radius: 3px;")
                    rot_left_b.clicked.connect(lambda checked, i=iid: self.web_view.page().runJavaScript(f"rotateImage({i}, -15);"))
                    row.addWidget(rot_left_b)

                    rot_right_b = QPushButton("↷ 15°")
                    rot_right_b.setStyleSheet("background: #1E293B; color: #38BDF8; border: 1px solid #475569; font-size: 10px; padding: 3px 5px; border-radius: 3px;")
                    rot_right_b.clicked.connect(lambda checked, i=iid: self.web_view.page().runJavaScript(f"rotateImage({i}, 15);"))
                    row.addWidget(rot_right_b)

                    zin_b = QPushButton("➕")
                    zin_b.setStyleSheet("background: #1E293B; color: #38BDF8; border: 1px solid #475569; font-size: 10px; padding: 3px 6px; border-radius: 3px;")
                    zin_b.clicked.connect(lambda checked, i=iid: self.web_view.page().runJavaScript(f"scaleImage({i}, 1.25);"))
                    row.addWidget(zin_b)

                    zout_b = QPushButton("➖")
                    zout_b.setStyleSheet("background: #1E293B; color: #38BDF8; border: 1px solid #475569; font-size: 10px; padding: 3px 6px; border-radius: 3px;")
                    zout_b.clicked.connect(lambda checked, i=iid: self.web_view.page().runJavaScript(f"scaleImage({i}, 0.8);"))
                    row.addWidget(zout_b)

                    fly_b = QPushButton("🎯 Fly")
                    fly_b.setStyleSheet("background: #2563EB; color: #FFF; font-size: 10px; padding: 3px 8px; border-radius: 3px;")
                    fly_b.clicked.connect(lambda checked, i=iid: self.web_view.page().runJavaScript(f"flyToImage({i});"))
                    row.addWidget(fly_b)

                    del_b = QPushButton("🗑️ Del")
                    del_b.setStyleSheet("background: #7F1D1D; color: #FECACA; font-size: 10px; padding: 3px 8px; border-radius: 3px;")
                    del_b.clicked.connect(lambda checked, i=iid: self.web_view.page().runJavaScript(f"deleteImage({i});"))
                    row.addWidget(del_b)

                    item.setSizeHint(QSize(300, 36))
                    self.img_list_widget.addItem(item)
                    self.img_list_widget.setItemWidget(item, w)

            # Update Tab 3: Tactical Pins only if pins data actually changed
            pin_json = json.dumps(pins, sort_keys=True)
            if getattr(self, '_last_pin_hash', None) != pin_json:
                self._last_pin_hash = pin_json
                t2_text = f"🎯 Pins ({len(pins)})"
                if self.data_tabs.tabText(2) != t2_text:
                    self.data_tabs.setTabText(2, t2_text)
                self.pin_list_widget.clear()
                for p in pins:
                    item = QListWidgetItem()
                    w = QWidget()
                    row = QHBoxLayout(w)
                    row.setContentsMargins(6, 2, 6, 2)
                    row.setSpacing(6)

                    lbl_clean = html.escape(str(p.get('label', 'Pin')))
                    r_red = p.get('rRed', 0)
                    r_orange = p.get('rOrange', 0)
                    r_yellow = p.get('rYellow', 0)
                    lat_str = str(p.get('lat', '0'))
                    lon_str = str(p.get('lon', '0'))
                    info_text = f"<b>{lbl_clean}</b> (<span style='color:#FF6B6B; font-weight:bold;'>● {r_red}m</span> <span style='color:#FFAA33; font-weight:bold;'>● {r_orange}m</span> <span style='color:#FFFF66; font-weight:bold;'>● {r_yellow}m</span>) | 📍{lat_str},{lon_str}"
                    info = QLabel(info_text)
                    info.setStyleSheet("color: #FCD34D; font-size: 11px;")
                    row.addWidget(info, 1)

                    pid = p.get('id', '')
                    fly_b = QPushButton("🎯 Fly")
                    fly_b.setStyleSheet("background: #2563EB; color: #FFF; font-size: 10px; padding: 3px 8px; border-radius: 3px;")
                    fly_b.clicked.connect(lambda checked, i=pid: self.web_view.page().runJavaScript(f"flyToPin('{i}');"))
                    row.addWidget(fly_b)

                    del_b = QPushButton("🗑️ Del")
                    del_b.setStyleSheet("background: #7F1D1D; color: #FECACA; font-size: 10px; padding: 3px 8px; border-radius: 3px;")
                    del_b.clicked.connect(lambda checked, i=pid: self.web_view.page().runJavaScript(f"deletePin('{i}');"))
                    row.addWidget(del_b)

                    item.setSizeHint(QSize(420, 36))
                    self.pin_list_widget.addItem(item)
                    self.pin_list_widget.setItemWidget(item, w)

        except Exception as e:
            self.debug_log.append(f"⚠️ Panel update error: {e}")
        finally:
            self.data_tabs.setUpdatesEnabled(True)
            self.obj_list_widget.blockSignals(False)
            self.img_list_widget.blockSignals(False)
            self.pin_list_widget.blockSignals(False)

# =========================================================================
# 4. Entry Point
# =========================================================================
if __name__ == "__main__":
    active_port = run_auto_port_server()
    print(f"Server started on http://127.0.0.1:{active_port}")

    # Robust settings for QtWebEngine / Chromium GPU process on Windows
    os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu-watchdog --ignore-gpu-blocklist --no-sandbox"

    # Global unhandled exception guard to prevent application crash / silent exit
    def global_excepthook(exc_type, exc_value, exc_traceback):
        import traceback
        err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        try:
            print("CRITICAL EXCEPTION:", err_msg, file=sys.stderr)
        except Exception:
            pass
    sys.excepthook = global_excepthook

    app = QApplication(sys.argv)
    window = Cesium3DIsolatedConsole(target_port=active_port)
    window.show()
    sys.exit(app.exec())
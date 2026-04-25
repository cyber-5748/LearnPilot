from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index():
    return HTML_PAGE


HTML_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LearnPilot</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
      background: #f5f7fa;
      display: flex;
      height: 100vh;
      overflow: hidden;
    }

    /* ═══════════════════════════════════════
       侧边栏
    ═══════════════════════════════════════ */
    .sidebar {
      width: 240px;
      min-width: 240px;
      background: #12151f;
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }

    /* Logo 区 */
    .logo {
      padding: 24px 20px 16px;
      border-bottom: 1px solid rgba(255,255,255,0.07);
    }
    .logo-title {
      font-size: 18px;
      font-weight: 700;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 4px;
    }
    .logo-icon {
      width: 28px; height: 28px;
      background: linear-gradient(135deg, #1677ff, #0050b3);
      border-radius: 8px;
      display: flex; align-items: center; justify-content: center;
      font-size: 15px; flex-shrink: 0;
    }
    .logo-sub {
      font-size: 12px;
      color: rgba(255,255,255,0.4);
      padding-left: 36px;
    }

    /* 操作按钮区 */
    .sidebar-actions {
      padding: 14px 12px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      border-bottom: 1px solid rgba(255,255,255,0.07);
    }
    .action-btn {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 9px 12px;
      border-radius: 8px;
      font-size: 14px;
      color: rgba(255,255,255,0.75);
      cursor: pointer;
      border: none;
      background: transparent;
      width: 100%;
      text-align: left;
      transition: background 0.15s, color 0.15s;
    }
    .action-btn:hover   { background: rgba(255,255,255,0.08); color: #fff; }
    .action-btn .icon   { font-size: 16px; width: 20px; text-align: center; flex-shrink: 0; }
    .action-btn.primary {
      background: rgba(22, 119, 255, 0.2);
      color: #69b1ff;
      border: 1px solid rgba(22,119,255,0.3);
    }
    .action-btn.primary:hover { background: rgba(22,119,255,0.3); color: #91caff; }

    /* 历史列表区 */
    .sidebar-section {
      flex: 1;
      overflow-y: auto;
      padding: 10px 0;
      display: flex;
      flex-direction: column;
    }
    .sidebar-section::-webkit-scrollbar { width: 4px; }
    .sidebar-section::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }

    .section-group { margin-bottom: 4px; }
    .section-label {
      font-size: 11px;
      color: rgba(255,255,255,0.3);
      padding: 6px 16px 4px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .history-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 7px 12px 7px 16px;
      font-size: 13px;
      color: rgba(255,255,255,0.55);
      cursor: pointer;
      border-radius: 6px;
      margin: 0 8px;
      transition: background 0.15s, color 0.15s;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .history-item:hover  { background: rgba(255,255,255,0.07); color: rgba(255,255,255,0.85); }
    .history-item.active { background: rgba(22,119,255,0.18); color: #91caff; }
    .history-item .hi    { font-size: 13px; flex-shrink: 0; }
    .history-item .ht    { overflow: hidden; text-overflow: ellipsis; flex: 1; }
    .history-item .hacts {
      display: none;
      gap: 2px;
      flex-shrink: 0;
    }
    .history-item:hover .hacts { display: flex; }
    .hact {
      width: 22px; height: 22px;
      border: none; background: transparent;
      border-radius: 4px; cursor: pointer;
      font-size: 12px; color: rgba(255,255,255,0.45);
      display: flex; align-items: center; justify-content: center;
      transition: background 0.15s, color 0.15s;
    }
    .hact:hover { background: rgba(255,255,255,0.12); color: #fff; }
    .hact.del:hover { background: rgba(255,77,79,0.25); color: #ff7875; }
    .history-item.pinned .ht::before {
      content: '📌 ';
      font-size: 11px;
    }

    .empty-hint {
      font-size: 12px;
      color: rgba(255,255,255,0.2);
      padding: 4px 16px 8px;
      font-style: italic;
    }

    /* ═══════════════════════════════════════
       主内容区
    ═══════════════════════════════════════ */
    .main {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      background: #fff;
    }

    /* 顶部栏 */
    .topbar {
      height: 48px;
      border-bottom: 1px solid #f0f0f0;
      display: flex;
      align-items: center;
      padding: 0 24px;
      gap: 12px;
      flex-shrink: 0;
    }
    .topbar-title {
      font-size: 15px;
      font-weight: 600;
      color: #222;
    }
    .topbar-sub {
      font-size: 12px;
      color: #aaa;
    }

    /* 页面切换 */
    .page { display: none; flex: 1; flex-direction: column; overflow: hidden; }
    .page.active { display: flex; }

    /* ── 聊天页 ── */
    .messages {
      flex: 1;
      overflow-y: auto;
      padding: 24px 32px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .messages::-webkit-scrollbar { width: 5px; }
    .messages::-webkit-scrollbar-thumb { background: #e0e0e0; border-radius: 3px; }

    .msg { display: flex; gap: 12px; align-items: flex-start; }
    .msg.user { flex-direction: row-reverse; }

    .avatar {
      width: 34px; height: 34px;
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 15px; flex-shrink: 0;
    }
    .msg.ai   .avatar { background: #e8f4ff; }
    .msg.user .avatar { background: #1677ff; color: #fff; }

    .bubble {
      max-width: 68%;
      padding: 10px 14px;
      border-radius: 12px;
      font-size: 14px;
      line-height: 1.75;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .msg.ai   .bubble { background: #f5f7fa; color: #222; border-top-left-radius: 3px; }
    .msg.user .bubble { background: #1677ff; color: #fff; border-top-right-radius: 3px; }

    .typing span {
      display: inline-block; width: 6px; height: 6px;
      border-radius: 50%; background: #999; margin: 0 2px;
      animation: blink 1.2s infinite;
    }
    .typing span:nth-child(2) { animation-delay: 0.2s; }
    .typing span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes blink {
      0%,80%,100% { opacity: 0.2; transform: scale(0.8); }
      40%          { opacity: 1;   transform: scale(1); }
    }

    .input-area {
      padding: 16px 32px 20px;
      border-top: 1px solid #f0f0f0;
      display: flex;
      gap: 10px;
      align-items: flex-end;
    }
    textarea {
      flex: 1;
      border: 1px solid #e0e0e0;
      border-radius: 10px;
      padding: 10px 14px;
      font-size: 14px;
      font-family: inherit;
      resize: none;
      outline: none;
      line-height: 1.6;
      max-height: 120px;
      background: #fafafa;
      transition: border-color 0.2s, background 0.2s;
    }
    textarea:focus { border-color: #1677ff; background: #fff; }

    .send-btn {
      height: 40px; width: 40px;
      background: #1677ff; color: #fff;
      border: none; border-radius: 10px;
      font-size: 18px; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      transition: background 0.2s, transform 0.1s;
      flex-shrink: 0;
    }
    .send-btn:hover   { background: #4096ff; }
    .send-btn:active  { transform: scale(0.94); }
    .send-btn:disabled{ background: #c5d8ff; cursor: not-allowed; }

    .input-hint { font-size: 11px; color: #ccc; text-align: center; padding: 0 0 4px; }

    /* ── 学习计划页 ── */
    .plan-container {
      flex: 1;
      overflow-y: auto;
      padding: 32px;
      display: flex;
      flex-direction: column;
      gap: 20px;
      max-width: 800px;
      width: 100%;
      align-self: center;
    }
    .plan-container::-webkit-scrollbar { width: 5px; }
    .plan-container::-webkit-scrollbar-thumb { background: #e0e0e0; border-radius: 3px; }

    .plan-form { display: flex; flex-direction: column; gap: 20px; }
    .form-title {
      font-size: 17px; font-weight: 700; color: #1a1a1a;
      padding-bottom: 12px; border-bottom: 1px solid #f0f0f0;
    }
    .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .form-field { display: flex; flex-direction: column; gap: 6px; }
    .form-field.full { grid-column: 1 / -1; }
    .form-field label { font-size: 13px; font-weight: 600; color: #333; }
    .form-field .field-hint { font-size: 11px; color: #aaa; margin-top: -2px; }

    .form-field input[type="text"],
    .form-field select,
    .form-field textarea {
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      padding: 9px 12px;
      font-size: 14px;
      font-family: inherit;
      background: #fafafa;
      outline: none;
      transition: border-color 0.2s, background 0.2s;
      color: #222;
    }
    .form-field input[type="text"]:focus,
    .form-field select:focus,
    .form-field textarea:focus { border-color: #1677ff; background: #fff; }
    .form-field textarea { resize: none; line-height: 1.6; }
    .form-field select { cursor: pointer; }

    .level-options { display: flex; gap: 8px; flex-wrap: wrap; }
    .level-btn {
      padding: 6px 16px; border-radius: 20px; font-size: 13px; cursor: pointer;
      border: 1px solid #e0e0e0; background: #fafafa; color: #555;
      transition: all 0.15s;
    }
    .level-btn:hover   { border-color: #1677ff; color: #1677ff; background: #e8f4ff; }
    .level-btn.active  { border-color: #1677ff; color: #fff; background: #1677ff; }

    .plan-submit {
      height: 42px; padding: 0 32px;
      background: #1677ff; color: #fff;
      border: none; border-radius: 8px;
      font-size: 15px; font-weight: 600; cursor: pointer;
      transition: background 0.2s; align-self: flex-end;
    }
    .plan-submit:hover    { background: #4096ff; }
    .plan-submit:disabled { background: #c5d8ff; cursor: not-allowed; }

    #planLoading {
      display: none;
      padding: 20px;
      color: #888;
      font-size: 14px;
      text-align: center;
    }

    /* 计划卡片 */
    #planResult { display: none; }

    .plan-card { border: 1px solid #e8e8e8; border-radius: 12px; overflow: hidden; }
    .plan-header {
      background: linear-gradient(135deg, #1677ff, #003eb3);
      color: #fff;
      padding: 20px 24px;
    }
    .plan-header h2 { font-size: 18px; margin-bottom: 8px; }
    .plan-meta { display: flex; flex-wrap: wrap; gap: 8px; font-size: 12px; }
    .plan-meta span {
      background: rgba(255,255,255,0.18);
      padding: 3px 10px;
      border-radius: 20px;
    }
    .plan-summary {
      padding: 14px 24px;
      background: #f8faff;
      font-size: 13px;
      color: #555;
      border-bottom: 1px solid #edf0ff;
    }

    .phase-list { padding: 16px 24px; display: flex; flex-direction: column; gap: 12px; }
    .phase-item {
      padding: 14px 16px;
      background: #fafafa;
      border-radius: 8px;
      border-left: 3px solid #1677ff;
    }
    .phase-top {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 8px;
    }
    .phase-num {
      width: 24px; height: 24px;
      background: #1677ff; color: #fff;
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 12px; font-weight: 700; flex-shrink: 0;
    }
    .phase-title { font-weight: 600; font-size: 14px; flex: 1; }
    .phase-weeks { font-size: 12px; color: #888; background: #f0f0f0; padding: 2px 8px; border-radius: 4px; }
    .phase-goal  { font-size: 13px; color: #389e0d; margin-bottom: 6px; }
    .phase-topics { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 6px; }
    .topic-tag {
      font-size: 11px; background: #e8f4ff; color: #1677ff;
      padding: 2px 8px; border-radius: 4px;
    }
    .phase-daily     { font-size: 12px; color: #666; margin-bottom: 6px; }
    .phase-milestone { font-size: 12px; color: #d46b08; background: #fff7e6; padding: 4px 10px; border-radius: 4px; display: inline-block; }

    .plan-tips-box {
      padding: 16px 24px;
      background: #fffbe6;
      border-top: 1px solid #ffe58f;
    }
    .tips-title { font-weight: 600; font-size: 13px; color: #874d00; margin-bottom: 8px; }
    .plan-tips-box ul { padding-left: 16px; }
    .plan-tips-box li { font-size: 13px; color: #555; line-height: 1.8; }

    /* 拆解章节按钮 */
    .plan-actions {
      padding: 16px 24px;
      border-top: 1px solid #f0f0f0;
      display: flex;
      gap: 10px;
      justify-content: center;
    }
    .plan-action-btn {
      padding: 10px 28px; border-radius: 8px; font-size: 14px; font-weight: 600;
      cursor: pointer; border: none; transition: background 0.2s;
    }
    .plan-action-btn.primary { background: #1677ff; color: #fff; }
    .plan-action-btn.primary:hover { background: #4096ff; }
    .plan-action-btn.primary:disabled { background: #c5d8ff; cursor: not-allowed; }

    /* ── 章节大纲页 ── */
    .syllabus-container {
      flex: 1; overflow-y: auto; padding: 24px 32px;
      max-width: 860px; width: 100%; align-self: center;
    }
    .syllabus-container::-webkit-scrollbar { width: 5px; }
    .syllabus-container::-webkit-scrollbar-thumb { background: #e0e0e0; border-radius: 3px; }

    .syllabus-phase { margin-bottom: 24px; }
    .syllabus-phase-header {
      display: flex; align-items: center; gap: 10px;
      padding: 10px 0 8px; border-bottom: 1px solid #f0f0f0;
      margin-bottom: 10px; cursor: pointer;
    }
    .syllabus-phase-header:hover { opacity: 0.85; }
    .syllabus-phase-num {
      width: 26px; height: 26px; background: #1677ff; color: #fff;
      border-radius: 50%; display: flex; align-items: center; justify-content: center;
      font-size: 13px; font-weight: 700; flex-shrink: 0;
    }
    .syllabus-phase-title { font-size: 15px; font-weight: 600; flex: 1; }
    .syllabus-phase-count { font-size: 12px; color: #888; background: #f5f5f5; padding: 2px 10px; border-radius: 12px; }

    .lesson-list { display: flex; flex-direction: column; gap: 6px; }
    .lesson-item {
      display: flex; align-items: center; gap: 12px;
      padding: 10px 14px; border-radius: 8px;
      background: #fafafa; border: 1px solid #f0f0f0;
      cursor: pointer; transition: all 0.15s;
    }
    .lesson-item:hover { border-color: #1677ff; background: #f0f7ff; }
    .lesson-num {
      width: 28px; height: 28px; border-radius: 50%;
      background: #e8f4ff; color: #1677ff;
      display: flex; align-items: center; justify-content: center;
      font-size: 12px; font-weight: 700; flex-shrink: 0;
    }
    .lesson-info { flex: 1; min-width: 0; }
    .lesson-title { font-size: 14px; font-weight: 500; color: #222; }
    .lesson-meta { font-size: 12px; color: #999; margin-top: 2px; }
    .lesson-dur { font-size: 12px; color: #888; background: #f5f5f5; padding: 2px 8px; border-radius: 4px; flex-shrink: 0; }

    /* 课时详情 */
    .lesson-detail { padding: 24px 0; }
    .lesson-detail-header {
      display: flex; align-items: center; gap: 12px;
      margin-bottom: 20px; padding-bottom: 14px; border-bottom: 1px solid #f0f0f0;
    }
    .lesson-back {
      width: 32px; height: 32px; border-radius: 8px; border: 1px solid #e0e0e0;
      background: #fff; cursor: pointer; font-size: 14px;
      display: flex; align-items: center; justify-content: center;
      transition: all 0.15s; flex-shrink: 0;
    }
    .lesson-back:hover { border-color: #1677ff; color: #1677ff; }
    .lesson-detail-title { font-size: 17px; font-weight: 700; }
    .lesson-detail-dur { font-size: 12px; color: #888; background: #f5f5f5; padding: 3px 10px; border-radius: 12px; }

    .lesson-section { margin-bottom: 18px; }
    .lesson-section-title { font-size: 13px; font-weight: 600; color: #555; margin-bottom: 8px; }
    .lesson-section ul { padding-left: 18px; }
    .lesson-section li { font-size: 14px; line-height: 1.8; color: #333; }
    .lesson-prereq-tag {
      display: inline-block; font-size: 12px; background: #fff7e6; color: #d46b08;
      padding: 2px 8px; border-radius: 4px; margin-right: 4px;
    }

    /* ── 进度条 ── */
    .progress-bar-wrap {
      display: flex; align-items: center; gap: 12px;
      padding: 12px 16px; background: #f8faff; border-radius: 10px;
      margin-bottom: 20px; border: 1px solid #e8f0fe;
    }
    .progress-bar-outer {
      flex: 1; height: 10px; background: #e8e8e8; border-radius: 5px; overflow: hidden;
    }
    .progress-bar-inner {
      height: 100%; background: linear-gradient(90deg, #1677ff, #36cfc9);
      border-radius: 5px; transition: width 0.5s ease;
    }
    .progress-text { font-size: 13px; font-weight: 600; color: #1677ff; white-space: nowrap; }
    .progress-stats {
      display: flex; gap: 16px; font-size: 12px; color: #888;
    }

    /* 课时状态标记 */
    .lesson-status {
      font-size: 11px; padding: 2px 8px; border-radius: 4px; flex-shrink: 0; font-weight: 500;
    }
    .lesson-status.not-started { background: #f5f5f5; color: #bbb; }
    .lesson-status.learned { background: #e8f4ff; color: #1677ff; }
    .lesson-status.passed { background: #f6ffed; color: #389e0d; }
    .lesson-status.failed { background: #fff2f0; color: #cf1322; }
    .lesson-score {
      font-size: 11px; color: #888; flex-shrink: 0;
    }

    /* ── 学习报告页 ── */
    .report-header {
      text-align: center; padding: 24px 0 20px;
      border-bottom: 1px solid #f0f0f0; margin-bottom: 24px;
    }
    .report-header h2 { font-size: 20px; font-weight: 700; color: #222; margin-bottom: 8px; }
    .report-score-ring {
      width: 120px; height: 120px; margin: 16px auto;
      border-radius: 50%; display: flex; align-items: center; justify-content: center;
      font-size: 32px; font-weight: 700; border: 6px solid #e8e8e8;
    }
    .report-score-ring.good { border-color: #389e0d; color: #389e0d; }
    .report-score-ring.ok   { border-color: #d48806; color: #d48806; }
    .report-score-ring.bad  { border-color: #cf1322; color: #cf1322; }
    .report-stats {
      display: flex; justify-content: center; gap: 32px; margin-top: 12px;
    }
    .report-stat { text-align: center; }
    .report-stat-num { font-size: 22px; font-weight: 700; color: #222; }
    .report-stat-label { font-size: 12px; color: #888; margin-top: 2px; }

    .report-section { margin-bottom: 24px; }
    .report-section-title {
      font-size: 15px; font-weight: 700; color: #222;
      padding-bottom: 8px; border-bottom: 1px solid #f0f0f0; margin-bottom: 12px;
    }
    .report-lesson-row {
      display: flex; align-items: center; gap: 10px;
      padding: 8px 12px; border-radius: 8px; margin-bottom: 4px;
    }
    .report-lesson-row.passed { background: #f6ffed; }
    .report-lesson-row.failed { background: #fff2f0; }
    .report-lesson-idx {
      width: 24px; height: 24px; border-radius: 50%; font-size: 11px; font-weight: 700;
      display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }
    .report-lesson-row.passed .report-lesson-idx { background: #b7eb8f; color: #135200; }
    .report-lesson-row.failed .report-lesson-idx { background: #ffa39e; color: #820014; }
    .report-lesson-title { flex: 1; font-size: 13px; color: #333; }
    .report-lesson-score { font-size: 13px; font-weight: 600; }
    .report-lesson-row.passed .report-lesson-score { color: #389e0d; }
    .report-lesson-row.failed .report-lesson-score { color: #cf1322; }

    .report-tags { display: flex; flex-wrap: wrap; gap: 6px; }
    .report-tag {
      font-size: 12px; padding: 4px 12px; border-radius: 16px;
    }
    .report-tag.weak { background: #fff2f0; color: #cf1322; border: 1px solid #ffa39e; }
    .report-tag.strong { background: #f6ffed; color: #389e0d; border: 1px solid #b7eb8f; }

    .report-suggestion {
      padding: 10px 14px; background: #f8faff; border-radius: 8px;
      border-left: 3px solid #1677ff; margin-bottom: 8px;
      font-size: 14px; line-height: 1.8; color: #333;
    }
    .report-summary {
      padding: 16px 20px; background: #fffbe6; border-radius: 10px;
      border: 1px solid #ffe58f; font-size: 14px; line-height: 1.9; color: #555;
    }

    /* ── 资料库页 ── */
    .books-container {
      flex: 1; overflow-y: auto; padding: 32px;
      max-width: 800px; width: 100%; align-self: center;
    }
    .books-header {
      display: flex; align-items: center; justify-content: space-between;
      margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid #f0f0f0;
    }
    .books-header h2 { font-size: 18px; font-weight: 700; color: #222; }
    .upload-area {
      border: 2px dashed #d9d9d9; border-radius: 12px; padding: 32px;
      text-align: center; cursor: pointer; transition: all 0.2s;
      margin-bottom: 24px; background: #fafafa;
    }
    .upload-area:hover { border-color: #1677ff; background: #f0f7ff; }
    .upload-area.dragging { border-color: #1677ff; background: #e6f0ff; }
    .upload-icon { font-size: 36px; margin-bottom: 8px; }
    .upload-text { font-size: 14px; color: #555; margin-bottom: 4px; }
    .upload-hint { font-size: 12px; color: #999; }
    .upload-progress {
      margin-top: 12px; display: none;
    }
    .upload-progress .bar {
      height: 4px; background: #f0f0f0; border-radius: 2px; overflow: hidden;
    }
    .upload-progress .bar-fill {
      height: 100%; background: #1677ff; border-radius: 2px;
      transition: width 0.3s; width: 0%;
    }
    .upload-progress .status { font-size: 12px; color: #888; margin-top: 6px; }
    .book-list { display: flex; flex-direction: column; gap: 8px; }
    .book-card {
      display: flex; align-items: center; gap: 14px;
      padding: 14px 16px; background: #fff; border: 1px solid #f0f0f0;
      border-radius: 10px; transition: box-shadow 0.15s;
    }
    .book-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
    .book-icon {
      width: 40px; height: 40px; border-radius: 8px;
      display: flex; align-items: center; justify-content: center;
      font-size: 20px; flex-shrink: 0;
    }
    .book-icon.txt  { background: #f0f7ff; }
    .book-icon.md   { background: #f6ffed; }
    .book-icon.epub { background: #fff7e6; }
    .book-info { flex: 1; min-width: 0; }
    .book-title { font-size: 14px; font-weight: 600; color: #222; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .book-meta { font-size: 12px; color: #999; margin-top: 2px; }
    .book-delete {
      padding: 4px 10px; border: 1px solid #ffa39e; border-radius: 6px;
      background: #fff; color: #cf1322; font-size: 12px; cursor: pointer;
      transition: all 0.15s;
    }
    .book-delete:hover { background: #fff2f0; }
    .books-empty { text-align: center; padding: 48px 0; color: #bbb; font-size: 14px; }

    /* ── 作业页 ── */
    .homework-section { margin-top: 24px; padding-top: 20px; border-top: 2px solid #f0f0f0; }
    .homework-title { font-size: 16px; font-weight: 700; color: #222; margin-bottom: 16px; }
    .hw-question {
      padding: 16px; margin-bottom: 12px; background: #fafafa;
      border: 1px solid #f0f0f0; border-radius: 10px;
    }
    .hw-question.correct { border-color: #b7eb8f; background: #f6ffed; }
    .hw-question.wrong   { border-color: #ffa39e; background: #fff2f0; }
    .hw-q-header {
      display: flex; align-items: center; gap: 8px; margin-bottom: 10px;
    }
    .hw-q-num {
      width: 26px; height: 26px; border-radius: 50%; background: #1677ff; color: #fff;
      display: flex; align-items: center; justify-content: center;
      font-size: 12px; font-weight: 700; flex-shrink: 0;
    }
    .hw-q-type {
      font-size: 11px; padding: 2px 8px; border-radius: 4px;
      background: #e8f4ff; color: #1677ff;
    }
    .hw-q-points { font-size: 12px; color: #888; margin-left: auto; }
    .hw-q-text { font-size: 14px; line-height: 1.8; color: #333; margin-bottom: 10px; }

    .hw-options { display: flex; flex-direction: column; gap: 6px; }
    .hw-option {
      display: flex; align-items: center; gap: 10px;
      padding: 8px 12px; border-radius: 8px; border: 1px solid #e8e8e8;
      cursor: pointer; font-size: 14px; transition: all 0.15s;
    }
    .hw-option:hover { border-color: #1677ff; background: #f0f7ff; }
    .hw-option.selected { border-color: #1677ff; background: #e8f4ff; color: #1677ff; font-weight: 500; }
    .hw-option-radio {
      width: 18px; height: 18px; border-radius: 50%; border: 2px solid #d9d9d9;
      display: flex; align-items: center; justify-content: center; flex-shrink: 0;
      transition: border-color 0.15s;
    }
    .hw-option.selected .hw-option-radio {
      border-color: #1677ff;
    }
    .hw-option.selected .hw-option-radio::after {
      content: ''; width: 10px; height: 10px; border-radius: 50%; background: #1677ff;
    }

    .hw-textarea {
      width: 100%; min-height: 80px; border: 1px solid #e0e0e0; border-radius: 8px;
      padding: 10px 12px; font-size: 14px; font-family: inherit;
      resize: vertical; outline: none; background: #fff;
      transition: border-color 0.2s;
    }
    .hw-textarea:focus { border-color: #1677ff; }

    .hw-submit-bar {
      display: flex; align-items: center; gap: 12px;
      margin-top: 20px; padding-top: 16px; border-top: 1px solid #f0f0f0;
    }
    .hw-submit-btn {
      padding: 10px 32px; border-radius: 8px; font-size: 15px; font-weight: 600;
      cursor: pointer; border: none; background: #1677ff; color: #fff;
      transition: background 0.2s;
    }
    .hw-submit-btn:hover { background: #4096ff; }
    .hw-submit-btn:disabled { background: #c5d8ff; cursor: not-allowed; }

    .hw-result-banner {
      padding: 16px 20px; border-radius: 10px; margin-bottom: 16px;
      display: flex; align-items: center; gap: 16px;
    }
    .hw-result-banner.passed { background: #f6ffed; border: 1px solid #b7eb8f; }
    .hw-result-banner.failed { background: #fff2f0; border: 1px solid #ffa39e; }
    .hw-score { font-size: 28px; font-weight: 700; }
    .hw-result-banner.passed .hw-score { color: #389e0d; }
    .hw-result-banner.failed .hw-score { color: #cf1322; }
    .hw-result-info { flex: 1; }
    .hw-result-status { font-size: 15px; font-weight: 600; }
    .hw-result-banner.passed .hw-result-status { color: #389e0d; }
    .hw-result-banner.failed .hw-result-status { color: #cf1322; }
    .hw-feedback {
      font-size: 13px; color: #555; line-height: 1.7; margin-top: 6px;
      padding: 8px 12px; background: #f8faff; border-radius: 6px;
      border-left: 3px solid #1677ff;
    }
    .hw-weak-points {
      display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px;
    }
    .hw-weak-tag {
      font-size: 12px; padding: 3px 10px; border-radius: 4px;
      background: #fff7e6; color: #d46b08; border: 1px solid #ffe58f;
    }
  </style>
</head>
<body>

<!-- ── 侧边栏 ── -->
<div class="sidebar">
  <div class="logo">
    <div class="logo-title">
      <div class="logo-icon">🎓</div>
      LearnPilot
    </div>
    <div class="logo-sub">AI 驱动的个人私教</div>
  </div>

  <div class="sidebar-actions">
    <button class="action-btn primary" onclick="newChat()">
      <span class="icon">✏️</span> 新对话
    </button>
    <button class="action-btn" onclick="newPlan()">
      <span class="icon">📋</span> 新学习计划
    </button>
    <button class="action-btn" onclick="showBooks()">
      <span class="icon">📚</span> 资料库
    </button>
  </div>

  <div class="sidebar-section">
    <div class="section-group">
      <div class="section-label">历史对话</div>
      <div id="sessionList"><div class="empty-hint">暂无历史对话</div></div>
    </div>

    <div class="section-group" style="margin-top:8px;">
      <div class="section-label">学习计划</div>
      <div id="planList"><div class="empty-hint">暂无学习计划</div></div>
    </div>
  </div>
</div>

<!-- ── 主内容区 ── -->
<div class="main">
  <div class="topbar">
    <div class="topbar-title" id="topbarTitle">新对话</div>
    <div class="topbar-sub"  id="topbarSub"></div>
  </div>

  <!-- 聊天页 -->
  <div class="page active" id="chatPage">
    <div class="messages" id="messages">
      <div class="msg ai">
        <div class="avatar">🤖</div>
        <div class="bubble">你好！我是 LearnPilot，你的 AI 私教。<br>有什么想学的，直接问我吧 😊</div>
      </div>
    </div>
    <div class="input-area">
      <textarea id="chatInput" rows="1" placeholder="输入问题，Enter 发送…"></textarea>
      <button class="send-btn" id="sendBtn" onclick="sendMessage()">➤</button>
    </div>
    <p class="input-hint">Enter 发送</p>
  </div>

  <!-- 学习计划页 -->
  <div class="page" id="planPage">
    <div class="plan-container">
      <div class="plan-form" id="planInputGroup">
        <div class="form-title">📋 填写学习需求</div>

        <div class="form-field full">
          <label>想学什么？</label>
          <div class="field-hint">填写具体的技术方向或技能</div>
          <input type="text" id="fieldGoal" placeholder="例如：AI Agent 开发、FastAPI、Python 数据分析…" />
        </div>

        <div class="form-row">
          <div class="form-field">
            <label>当前基础水平</label>
            <div class="level-options">
              <div class="level-btn active" data-level="零基础"  onclick="selectLevel(this)">零基础</div>
              <div class="level-btn"        data-level="初级"    onclick="selectLevel(this)">初级</div>
              <div class="level-btn"        data-level="中级"    onclick="selectLevel(this)">中级</div>
              <div class="level-btn"        data-level="高级"    onclick="selectLevel(this)">高级</div>
            </div>
          </div>

          <div class="form-field">
            <label>学习用途</label>
            <select id="fieldPurpose">
              <option value="求职">求职 / 找工作</option>
              <option value="项目开发">项目开发</option>
              <option value="兴趣学习">兴趣学习</option>
              <option value="考试备考">考试备考</option>
              <option value="技能提升">技能提升</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-field">
            <label>学习周期</label>
            <select id="fieldWeeks" onchange="onWeeksChange(this)">
              <option value="2周">2 周</option>
              <option value="1个月">1 个月</option>
              <option value="2个月" selected>2 个月</option>
              <option value="3个月">3 个月</option>
              <option value="6个月">6 个月</option>
              <option value="custom">自定义…</option>
            </select>
            <input type="text" id="fieldWeeksCustom" placeholder="例如：45天、10周"
              style="display:none; margin-top:6px;" />
          </div>

          <div class="form-field">
            <label>每日学习时间</label>
            <select id="fieldHours">
              <option value="0.5小时">0.5 小时</option>
              <option value="1小时">1 小时</option>
              <option value="1.5小时" selected>1.5 小时</option>
              <option value="2小时">2 小时</option>
              <option value="3小时">3 小时</option>
              <option value="4小时以上">4 小时以上</option>
            </select>
          </div>
        </div>

        <div class="form-field full">
          <label>补充说明（选填）</label>
          <div class="field-hint">如有特殊情况或目标，可以在这里补充</div>
          <textarea id="fieldExtra" rows="2" placeholder="例如：准备3个月后的面试、已经会Java想转Python…"></textarea>
        </div>

        <div class="form-field full">
          <label>参考书籍（选填）</label>
          <div class="field-hint">选择已上传的书籍，计划和课件将严格参考书籍的知识结构</div>
          <select id="fieldBook">
            <option value="">不使用参考书籍</option>
          </select>
        </div>

        <button class="plan-submit" id="planBtn" onclick="generatePlan()">生成学习计划</button>
      </div>
      <div id="planLoading">⏳ 正在解析需求并生成计划，约需 15 秒…</div>
      <div id="planResult"></div>
    </div>
  </div>

  <!-- 章节大纲页 -->
  <div class="page" id="syllabusPage">
    <div class="syllabus-container" id="syllabusContent">
    </div>
  </div>

  <!-- 资料库页 -->
  <div class="page" id="booksPage">
    <div class="books-container">
      <div class="books-header">
        <h2>📚 学习资料库</h2>
      </div>
      <div class="upload-area" id="uploadArea" onclick="document.getElementById('fileInput').click()">
        <div class="upload-icon">📄</div>
        <div class="upload-text">点击或拖拽文件到此处上传</div>
        <div class="upload-hint">支持 .txt / .md / .epub 格式，最大 50MB</div>
        <input type="file" id="fileInput" accept=".txt,.md,.epub" style="display:none" />
        <div class="upload-progress" id="uploadProgress">
          <div class="bar"><div class="bar-fill" id="uploadBar"></div></div>
          <div class="status" id="uploadStatus">上传中…</div>
        </div>
      </div>
      <div class="book-list" id="bookList">
        <div class="books-empty">暂无上传资料</div>
      </div>
    </div>
  </div>

  <!-- 学习报告页 -->
  <div class="page" id="reportPage">
    <div class="syllabus-container" id="reportContent">
    </div>
  </div>
</div>

<script>
// ── 状态 ─────────────────────────────────────────────────────
let sessionId    = localStorage.getItem('learnpilot_session_id') || null;
let currentView  = 'chat';
let planCount    = 0;

// ── 初始化 ────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  loadSessions();
  loadPlans();
  if (sessionId) loadSession(sessionId, false);
});

// ── 侧边栏：加载历史会话 ──────────────────────────────────────
async function loadSessions() {
  try {
    const res = await fetch('/sessions');
    const list = await res.json();
    const el = document.getElementById('sessionList');
    if (!list.length) { 
      el.innerHTML = '<div class="empty-hint">暂无历史对话</div>'; 
      return; 
    }
    el.innerHTML = list.map(s => `
      <div class="history-item ${s.session_id === sessionId ? 'active' : ''} ${s.pinned ? 'pinned' : ''}"
           id="si-${s.session_id}">
        <span class="hi">💬</span>
        <span class="ht" onclick="loadSession('${s.session_id}', true)">${escHtml(s.preview || '')}</span>
        <div class="hacts">
          <button class="hact" title="重命名" onclick="renameSession('${s.session_id}', this)">✏️</button>
          <button class="hact" title="${s.pinned ? '取消置顶' : '置顶'}" onclick="togglePinSession('${s.session_id}', ${s.pinned}, this)">📌</button>
          <button class="hact del" title="删除" onclick="deleteSession('${s.session_id}')">🗑️</button>
        </div>
      </div>`).join('');
  } catch(e) { 
    console.error(e); 
  }
}

async function renameSession(sid, btn) {
  const item = document.getElementById('si-' + sid);
  const ht   = item.querySelector('.ht');
  const name = prompt('重命名对话', ht.textContent.trim());
  if (!name || !name.trim()) return;
  await fetch(`/sessions/${sid}/rename`, {
    method: 'PATCH', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name: name.trim()}),
  });
  ht.textContent = name.trim();
}

async function togglePinSession(sid, isPinned, btn) {
  const newPinned = !isPinned;
  await fetch(`/sessions/${sid}/pin?pinned=${newPinned}`, {method: 'PATCH'});
  btn.title = newPinned ? '取消置顶' : '置顶';
  btn.setAttribute('onclick', `togglePinSession('${sid}', ${newPinned}, this)`);
  document.getElementById('si-' + sid).classList.toggle('pinned', newPinned);
  loadSessions();
}

async function deleteSession(sid) {
  if (!confirm('确认删除这条对话？操作不可恢复。')) return;
  await fetch(`/sessions/${sid}`, {method: 'DELETE'});
  if (sessionId === sid) {
    sessionId = null;
    localStorage.removeItem('learnpilot_session_id');
    newChat();
  }
  loadSessions();
}

// ── 切换到某个历史会话 ────────────────────────────────────────
async function loadSession(sid, switchView) {
  sessionId = sid;
  localStorage.setItem('learnpilot_session_id', sid);

  // 高亮侧边栏
  document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
  const item = document.getElementById('si-' + sid);
  if (item) item.classList.add('active');

  // 加载消息并渲染
  try {
    const res  = await fetch('/sessions/' + sid);
    const data = await res.json();
    const msgs = data.messages || [];
    const box  = document.getElementById('messages');
    box.innerHTML = msgs.length
      ? msgs.map(m => msgHtml(m.role === 'user' ? 'user' : 'ai', escHtml(m.content))).join('')
      : '<div class="msg ai"><div class="avatar">🤖</div><div class="bubble">你好！继续上次的对话 😊</div></div>';
    box.scrollTop = box.scrollHeight;
  } catch(e) {}

  if (switchView) showPage('chat');
  setTopbar('对话', sid.slice(0, 8) + '…');
}

// ── 新对话 ────────────────────────────────────────────────────
function newChat() {
  sessionId = null;
  localStorage.removeItem('learnpilot_session_id');
  document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
  document.getElementById('messages').innerHTML = `
    <div class="msg ai">
      <div class="avatar">🤖</div>
      <div class="bubble">你好！我是 LearnPilot，你的 AI 私教。<br>有什么想学的，直接问我吧 😊</div>
    </div>`;
  showPage('chat');
  setTopbar('新对话', '');
  document.getElementById('chatInput').focus();
}

// ── 新学习计划 ────────────────────────────────────────────────
function newPlan() {
  document.getElementById('planInputGroup').style.display = 'flex';
  document.getElementById('fieldGoal').value    = '';
  document.getElementById('fieldExtra').value   = '';
  document.getElementById('fieldWeeks').value        = '2个月';
  document.getElementById('fieldWeeksCustom').style.display = 'none';
  document.getElementById('fieldWeeksCustom').value  = '';
  document.getElementById('fieldHours').value   = '1.5小时';
  document.getElementById('fieldPurpose').value = '求职';
  // 重置水平选择
  document.querySelectorAll('.level-btn').forEach(b => b.classList.remove('active'));
  document.querySelector('.level-btn[data-level="零基础"]').classList.add('active');
  document.getElementById('fieldBook').value   = '';
  document.getElementById('planResult').style.display  = 'none';
  document.getElementById('planLoading').style.display = 'none';
  showPage('plan');
  setTopbar('新学习计划', '');
  loadBookOptions();
  document.getElementById('fieldGoal').focus();
}

function selectLevel(el) {
  document.querySelectorAll('.level-btn').forEach(b => b.classList.remove('active'));
  el.classList.add('active');
}

function onWeeksChange(sel) {
  const custom = document.getElementById('fieldWeeksCustom');
  if (sel.value === 'custom') {
    custom.style.display = 'block';
    custom.focus();
  } else {
    custom.style.display = 'none';
    custom.value = '';
  }
}

// ── 页面切换 ──────────────────────────────────────────────────
function showPage(name) {
  currentView = name;
  document.getElementById('chatPage').classList.toggle('active', name === 'chat');
  document.getElementById('planPage').classList.toggle('active', name === 'plan');
  document.getElementById('syllabusPage').classList.toggle('active', name === 'syllabus');
  document.getElementById('booksPage').classList.toggle('active', name === 'books');
  document.getElementById('reportPage').classList.toggle('active', name === 'report');
}

function setTopbar(title, sub) {
  document.getElementById('topbarTitle').textContent = title;
  document.getElementById('topbarSub').textContent   = sub;
}

// ── 聊天 ──────────────────────────────────────────────────────
const chatInput = document.getElementById('chatInput');
chatInput.addEventListener('input', () => {
  chatInput.style.height = 'auto';
  chatInput.style.height = chatInput.scrollHeight + 'px';
});
chatInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

function msgHtml(role, text) {
  return `<div class="msg ${role}">
    <div class="avatar">${role === 'user' ? '🙋' : '🤖'}</div>
    <div class="bubble">${text}</div>
  </div>`;
}

function appendMsg(role, text) {
  const box = document.getElementById('messages');
  box.insertAdjacentHTML('beforeend', msgHtml(role, text));
  box.scrollTop = box.scrollHeight;
}

function showTyping() {
  const box = document.getElementById('messages');
  box.insertAdjacentHTML('beforeend', `
    <div class="msg ai" id="typing">
      <div class="avatar">🤖</div>
      <div class="bubble typing"><span></span><span></span><span></span></div>
    </div>`);
  box.scrollTop = box.scrollHeight;
}
function removeTyping() {
  const el = document.getElementById('typing');
  if (el) el.remove();
}

async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text) return;
  appendMsg('user', escHtml(text));
  chatInput.value = ''; chatInput.style.height = 'auto';
  document.getElementById('sendBtn').disabled = true;
  showTyping();

  try {
    const res = await fetch('/chat/stream', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: text, session_id: sessionId}),
    });

    const reader  = res.body.getReader();
    const decoder = new TextDecoder();
    let   buffer  = '';
    let   bubble  = null;   // 流式 AI 气泡
    let   isNew   = !sessionId;

    while (true) {
      const {done, value} = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, {stream: true});
      const lines = buffer.split('\\n');
      buffer = lines.pop();   // 保留不完整的行

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        let evt;
        try { evt = JSON.parse(line.slice(6)); } catch { continue; }

        if (evt.type === 'start') {
          // 收到 session_id，移除 typing，创建空气泡
          removeTyping();
          sessionId = evt.session_id;
          localStorage.setItem('learnpilot_session_id', sessionId);
          setTopbar('对话', sessionId.slice(0, 8) + '…');

          const box = document.getElementById('messages');
          box.insertAdjacentHTML('beforeend', `
            <div class="msg ai" id="stream-bubble">
              <div class="avatar">🤖</div>
              <div class="bubble" id="stream-text"></div>
            </div>`);
          box.scrollTop = box.scrollHeight;
          bubble = document.getElementById('stream-text');
        } else if (evt.type === 'token' && bubble) {
          bubble.textContent += evt.token;
          document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
        } else if (evt.type === 'done') {
          if (isNew) loadSessions();
        } else if (evt.type === 'error') {
          removeTyping();
          if (bubble) bubble.textContent = '⚠️ ' + (evt.message || '请求失败');
          else appendMsg('ai', '⚠️ ' + (evt.message || '请求失败'));
        }
      }
    }

    // 流结束后把气泡 id 去掉（保留内容）
    const sb = document.getElementById('stream-bubble');
    if (sb) sb.removeAttribute('id');
    const st = document.getElementById('stream-text');
    if (st) st.removeAttribute('id');

  } catch {
    removeTyping();
    appendMsg('ai', '⚠️ 请求失败，请检查服务是否正常。');
  }
  document.getElementById('sendBtn').disabled = false;
  chatInput.focus();
}

// ── 学习计划 ──────────────────────────────────────────────────
async function generatePlan() {
  const goal    = document.getElementById('fieldGoal').value.trim();
  const level   = document.querySelector('.level-btn.active')?.dataset.level || '零基础';
  const weeksRaw = document.getElementById('fieldWeeks').value;
  const weeks   = weeksRaw === 'custom'
    ? (document.getElementById('fieldWeeksCustom').value.trim() || '2个月')
    : weeksRaw;
  const hours   = document.getElementById('fieldHours').value;
  const purpose = document.getElementById('fieldPurpose').value;
  const extra   = document.getElementById('fieldExtra').value.trim();

  if (!goal) {
    document.getElementById('fieldGoal').focus();
    document.getElementById('fieldGoal').style.borderColor = '#ff4d4f';
    setTimeout(() => document.getElementById('fieldGoal').style.borderColor = '', 1500);
    return;
  }

  // 拼成自然语言，和之前的后端接口完全兼容
  const userInput = `${level}，${weeks}学${goal}，每天${hours}，用于${purpose}` +
                    (extra ? `，补充：${extra}` : '');

  const bookId = document.getElementById('fieldBook').value;

  document.getElementById('planBtn').disabled    = true;
  document.getElementById('planResult').style.display  = 'none';
  document.getElementById('planLoading').style.display = 'block';

  try {
    const body = {user_input: userInput};
    if (bookId) body.book_id = parseInt(bookId);
    const res  = await fetch('/plan', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body),
    });
    const plan = await res.json();
    document.getElementById('planLoading').style.display = 'none';
    if (plan.detail) {
      showPlanError(plan.detail);
    } else {
      currentPlanId = plan.plan_id;
      currentSyllabus = null;
      renderPlan(plan, userInput);
      addPlanToSidebar();
    }
  } catch {
    document.getElementById('planLoading').style.display = 'none';
    showPlanError('生成失败，请重试。');
  }
  document.getElementById('planBtn').disabled = false;
}

function showPlanError(msg) {
  const el = document.getElementById('planResult');
  el.style.display = 'block';
  el.innerHTML = `<p style="color:#ff4d4f;padding:12px">⚠️ ${msg}</p>`;
}

// ── 侧边栏：加载历史计划 ──────────────────────────────────────
async function loadPlans() {
  try {
    const res  = await fetch('/plans');
    const list = await res.json();
    renderPlanSidebar(list);
  } catch(e) { console.error(e); }
}

function renderPlanSidebar(list) {
  const el = document.getElementById('planList');
  if (!list.length) { 
    el.innerHTML = '<div class="empty-hint">暂无学习计划</div>'; 
    return; 
  }
  el.innerHTML = list.map(p => `
    <div class="history-item ${p.pinned ? 'pinned' : ''}" id="pi-${p.id}">
      <span class="hi">📋</span>
      <span class="ht" onclick="viewPlan(${p.id})">${escHtml(p.title || '')}</span>
      <div class="hacts">
        <button class="hact" title="重命名" onclick="renamePlan(${p.id}, this)">✏️</button>
        <button class="hact" title="${p.pinned ? '取消置顶' : '置顶'}" onclick="togglePinPlan(${p.id}, ${p.pinned}, this)">📌</button>
        <button class="hact del" title="删除" onclick="deletePlan(${p.id})">🗑️</button>
      </div>
    </div>`).join('');
}

async function renamePlan(pid, btn) {
  const item = document.getElementById('pi-' + pid);
  const ht   = item.querySelector('.ht');
  const name = prompt('重命名学习计划', ht.textContent.trim());
  if (!name || !name.trim()) return;
  await fetch(`/plans/${pid}/rename`, {
    method: 'PATCH', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({title: name.trim()}),
  });
  ht.textContent = name.trim();
}

async function togglePinPlan(pid, isPinned, btn) {
  const newPinned = !isPinned;
  await fetch(`/plans/${pid}/pin?pinned=${newPinned}`, {method: 'PATCH'});
  btn.title = newPinned ? '取消置顶' : '置顶';
  btn.setAttribute('onclick', `togglePinPlan(${pid}, ${newPinned}, this)`);
  document.getElementById('pi-' + pid).classList.toggle('pinned', newPinned);
  loadPlans();
}

async function deletePlan(pid) {
  if (!confirm('确认删除这条学习计划？操作不可恢复。')) return;
  await fetch(`/plans/${pid}`, {method: 'DELETE'});
  loadPlans();
  // 如果当前正在展示这条计划，清空主区
  document.getElementById('planResult').style.display = 'none';
}

// 点击侧边栏历史计划，查看完整内容
async function viewPlan(planId) {
  showPage('plan');
  document.getElementById('planInputGroup').style.display = 'none';
  document.getElementById('planResult').style.display     = 'none';
  document.getElementById('planLoading').style.display    = 'block';
  document.getElementById('planBtn').disabled = true;

  try {
    const res  = await fetch('/plans/' + planId);
    const data = await res.json();
    document.getElementById('planLoading').style.display = 'none';
    renderPlan(data.plan, data.user_input);
    setTopbar(data.plan.title, data.created_at);
  } catch {
    document.getElementById('planLoading').style.display = 'none';
    showPlanError('加载失败，请重试。');
  }
  document.getElementById('planBtn').disabled = false;
}

function addPlanToSidebar() {
  // 重新从后端拉取，保证侧边栏和数据库同步
  loadPlans();
}

function renderPlan(plan, input) {
  const phasesHtml = plan.phases.map(p => `
    <div class="phase-item">
      <div class="phase-top">
        <div class="phase-num">${p.phase}</div>
        <div class="phase-title">${escHtml(p.title)}</div>
        <div class="phase-weeks">${escHtml(p.weeks)}</div>
      </div>
      <div class="phase-goal">🎯 ${escHtml(p.goal)}</div>
      <div class="phase-topics">${p.topics.map(t => `<span class="topic-tag">${escHtml(t)}</span>`).join('')}</div>
      <div class="phase-daily">⏰ ${escHtml(p.daily_plan)}</div>
      <span class="phase-milestone">🏆 ${escHtml(p.milestone)}</span>
    </div>`).join('');

  const tipsHtml = plan.tips.map(t => `<li>${escHtml(t)}</li>`).join('');

  const el = document.getElementById('planResult');
  el.style.display = 'block';
  el.innerHTML = `
    <div class="plan-card">
      <div class="plan-header">
        <h2>📚 ${escHtml(plan.title)}</h2>
        <div class="plan-meta">
          <span>起点：${escHtml(plan.level)}</span>
          <span>⏱ ${plan.total_weeks} 周 · ${plan.total_hours} 小时</span>
          <span>每天 ${plan.daily_hours} 小时</span>
        </div>
      </div>
      <div class="plan-summary">💡 ${escHtml(plan.summary)}</div>
      <div class="phase-list">${phasesHtml}</div>
      <div class="plan-tips-box">
        <div class="tips-title">📌 个性化建议</div>
        <ul>${tipsHtml}</ul>
      </div>
      <div class="plan-actions" id="planActions">
        <button class="plan-action-btn primary" id="syllabusBtn" onclick="expandSyllabus()">📖 拆解章节课时</button>
      </div>
    </div>`;
  setTopbar(plan.title, input.slice(0, 30) + '…');
}

// ── 章节拆解 ─────────────────────────────────────────────────
let currentPlanId = null;
let currentSyllabus = null;

// 在 renderPlan 被调用时记录 plan_id（从 viewPlan 跳入）
const _origViewPlan = viewPlan;
viewPlan = async function(planId) {
  currentPlanId = planId;
  await _origViewPlan(planId);
  // 查看是否已有拆解结果，有则显示"查看章节"而非"拆解"
  try {
    const res = await fetch('/plans/' + planId + '/syllabus');
    if (res.ok) {
      const data = await res.json();
      currentSyllabus = data.syllabus;
      const btn = document.getElementById('syllabusBtn');
      if (btn) { btn.textContent = '📖 查看章节课时'; btn.onclick = () => showSyllabus(planId); }
    }
  } catch {}
};

async function expandSyllabus() {
  if (!currentPlanId) return;
  const btn = document.getElementById('syllabusBtn');
  btn.disabled = true;
  btn.textContent = '⏳ 正在拆解章节…';

  try {
    const res = await fetch('/plans/' + currentPlanId + '/syllabus', { method: 'POST' });
    const data = await res.json();
    if (data.detail) {
      btn.textContent = '⚠️ ' + data.detail;
      setTimeout(() => { btn.textContent = '📖 拆解章节课时'; btn.disabled = false; }, 3000);
      return;
    }
    currentSyllabus = data;
    btn.textContent = '📖 查看章节课时';
    btn.disabled = false;
    btn.onclick = () => showSyllabus(currentPlanId);
    showSyllabus(currentPlanId);
  } catch {
    btn.textContent = '⚠️ 拆解失败，请重试';
    setTimeout(() => { btn.textContent = '📖 拆解章节课时'; btn.disabled = false; }, 3000);
  }
}

let currentProgress = {};

async function showSyllabus(planId) {
  if (!currentSyllabus) {
    try {
      const res = await fetch('/plans/' + planId + '/syllabus');
      if (!res.ok) return;
      const data = await res.json();
      currentSyllabus = data.syllabus;
    } catch { return; }
  }
  // 加载进度数据
  try {
    const res = await fetch('/plans/' + planId + '/progress');
    if (res.ok) currentProgress = await res.json();
    else currentProgress = {};
  } catch { currentProgress = {}; }

  renderSyllabus(currentSyllabus);
  showPage('syllabus');
  setTopbar(currentSyllabus.plan_title || '章节大纲', currentSyllabus.total_lessons + ' 个课时');
}

function renderSyllabus(syl) {
  const el = document.getElementById('syllabusContent');

  // 计算整体进度
  const total = syl.total_lessons;
  let learnedCount = 0;
  let passedCount = 0;
  Object.values(currentProgress).forEach(p => {
    if (p.has_content) learnedCount++;
    if (p.passed) passedCount++;
  });
  const pct = total > 0 ? Math.round((passedCount / total) * 100) : 0;

  const progressHtml = `
    <div class="progress-bar-wrap">
      <div style="font-size:14px;font-weight:600;color:#222;">学习进度</div>
      <div class="progress-bar-outer">
        <div class="progress-bar-inner" style="width:${pct}%"></div>
      </div>
      <div class="progress-text">${pct}%</div>
    </div>
    <div class="progress-stats">
      <span>📖 已学课件：${learnedCount}/${total}</span>
      <span>✅ 已通过作业：${passedCount}/${total}</span>
      <button onclick="viewReport()" style="margin-left:auto;padding:4px 14px;border-radius:6px;border:1px solid #1677ff;background:#fff;color:#1677ff;font-size:12px;font-weight:600;cursor:pointer;transition:all 0.15s;"
        onmouseover="this.style.background='#1677ff';this.style.color='#fff'"
        onmouseout="this.style.background='#fff';this.style.color='#1677ff'">📊 学习报告</button>
    </div>`;

  const phasesHtml = syl.phases.map(p => {
    const lessonsHtml = p.lessons.map(l => {
      const prog = currentProgress[String(l.lesson_index)] || {};
      let statusHtml = '<span class="lesson-status not-started">未开始</span>';
      let scoreHtml = '';
      if (prog.passed) {
        statusHtml = '<span class="lesson-status passed">已通过</span>';
        scoreHtml = '<span class="lesson-score">' + prog.best_score + '/' + prog.max_score + '</span>';
      } else if (prog.best_score !== null && prog.best_score !== undefined) {
        statusHtml = '<span class="lesson-status failed">未通过</span>';
        scoreHtml = '<span class="lesson-score">' + prog.best_score + '/' + prog.max_score + '</span>';
      } else if (prog.has_content) {
        statusHtml = '<span class="lesson-status learned">已学习</span>';
      }

      return `
      <div class="lesson-item" onclick="viewLesson(${JSON.stringify(l).replace(/"/g, '&quot;')})">
        <div class="lesson-num">${l.lesson_index}</div>
        <div class="lesson-info">
          <div class="lesson-title">${escHtml(l.title)}</div>
          <div class="lesson-meta">${l.topics.slice(0,3).map(t => escHtml(t)).join(' · ')}</div>
        </div>
        ${scoreHtml}
        ${statusHtml}
        <div class="lesson-dur">${l.duration_min} 分钟</div>
      </div>`;
    }).join('');

    return `
      <div class="syllabus-phase">
        <div class="syllabus-phase-header">
          <div class="syllabus-phase-num">${p.phase}</div>
          <div class="syllabus-phase-title">${escHtml(p.title)}</div>
          <div class="syllabus-phase-count">${p.lessons.length} 课时</div>
        </div>
        <div class="lesson-list">${lessonsHtml}</div>
      </div>`;
  }).join('');

  el.innerHTML = `
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">
      <button class="lesson-back" onclick="backToPlan()">←</button>
      <div style="font-size:17px;font-weight:700;">📖 ${escHtml(syl.plan_title)}</div>
      <div style="font-size:12px;color:#888;background:#f5f5f5;padding:3px 10px;border-radius:12px;">共 ${syl.total_lessons} 课时</div>
    </div>
    ${progressHtml}
    ${phasesHtml}`;
}

function backToPlan() {
  showPage('plan');
}

async function viewLesson(lesson) {
  const el = document.getElementById('syllabusContent');
  const prereqHtml = lesson.prerequisites && lesson.prerequisites.length
    ? lesson.prerequisites.map(p => `<span class="lesson-prereq-tag">需先完成课时 ${p}</span>`).join('')
    : '<span style="color:#aaa;font-size:13px;">无前置要求</span>';

  el.innerHTML = `
    <div class="lesson-detail">
      <div class="lesson-detail-header">
        <button class="lesson-back" onclick="renderSyllabus(currentSyllabus)">←</button>
        <div class="lesson-detail-title">课时 ${lesson.lesson_index}：${escHtml(lesson.title)}</div>
        <div class="lesson-detail-dur">${lesson.duration_min} 分钟</div>
      </div>
      <div class="lesson-section">
        <div class="lesson-section-title">🎯 学习目标</div>
        <ul>${lesson.objectives.map(o => `<li>${escHtml(o)}</li>`).join('')}</ul>
      </div>
      <div class="lesson-section">
        <div class="lesson-section-title">🔗 前置要求</div>
        <div>${prereqHtml}</div>
      </div>
      <div id="lessonCourseware" style="padding:20px 0;color:#888;font-size:14px;">⏳ 正在生成课件内容，请稍候...</div>
    </div>`;
  setTopbar('课时 ' + lesson.lesson_index, escHtml(lesson.title));

  try {
    const res = await fetch('/plans/' + currentPlanId + '/lessons/' + lesson.lesson_index + '/generate', { method: 'POST' });
    const data = await res.json();
    if (data.detail) {
      document.getElementById('lessonCourseware').innerHTML = '<p style="color:#ff4d4f;">⚠️ ' + escHtml(data.detail) + '</p>';
      return;
    }
    renderCourseware(data);
  } catch {
    document.getElementById('lessonCourseware').innerHTML = '<p style="color:#ff4d4f;">⚠️ 课件生成失败，请重试。</p>';
  }
}

function renderCourseware(content) {
  const cw = document.getElementById('lessonCourseware');

  const explanationHtml = simpleMd(content.explanation);

  let codeHtml = '';
  if (content.code_examples && content.code_examples.length) {
    codeHtml = '<div class="lesson-section"><div class="lesson-section-title">💻 示例代码</div>' +
      content.code_examples.map(ex => `
        <div style="margin-bottom:16px;">
          <div style="font-size:13px;font-weight:600;color:#333;margin-bottom:6px;">${escHtml(ex.title)}</div>
          <pre style="background:#1e1e2e;color:#cdd6f4;padding:14px 16px;border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.6;"><code>${escHtml(ex.code)}</code></pre>
          <div style="font-size:13px;color:#555;line-height:1.8;margin-top:6px;padding:8px 12px;background:#f8faff;border-radius:6px;border-left:3px solid #1677ff;">${simpleMd(ex.explanation)}</div>
        </div>`).join('') + '</div>';
  }

  const analogiesHtml = content.analogies && content.analogies.length
    ? '<div class="lesson-section"><div class="lesson-section-title">💡 生活类比</div><ul>' +
      content.analogies.map(a => `<li>${simpleMd(a)}</li>`).join('') + '</ul></div>'
    : '';

  const takeawaysHtml = '<div class="lesson-section"><div class="lesson-section-title">📌 核心要点</div><ul>' +
    content.key_takeaways.map(t => `<li style="font-weight:500;">${escHtml(t)}</li>`).join('') + '</ul></div>';

  const nextHtml = content.next_hint
    ? `<div style="margin-top:16px;padding:12px 16px;background:#f0f7ff;border-radius:8px;font-size:13px;color:#1677ff;">➡️ <strong>下一课预告：</strong>${escHtml(content.next_hint)}</div>`
    : '';

  cw.innerHTML = `
    <div class="lesson-section">
      <div class="lesson-section-title">📖 概念讲解</div>
      <div style="font-size:14px;line-height:1.85;color:#333;">${explanationHtml}</div>
    </div>
    ${codeHtml}
    ${analogiesHtml}
    ${takeawaysHtml}
    ${nextHtml}
    <div class="homework-section" id="homeworkArea">
      <button class="hw-submit-btn" id="hwGenBtn" onclick="generateHomework(${content.lesson_index})">📝 生成本课作业</button>
    </div>`;

  // 检查是否已有作业
  checkExistingHomework(content.lesson_index);
}

function simpleMd(text) {
  if (!text) return '';
  return escHtml(text)
    .replace(/^### (.+)$/gm, '<h4 style="margin:12px 0 6px;font-size:14px;">$1</h4>')
    .replace(/^## (.+)$/gm, '<h3 style="margin:16px 0 8px;font-size:15px;">$1</h3>')
    .replace(/^# (.+)$/gm, '<h2 style="margin:18px 0 8px;font-size:16px;">$1</h2>')
    .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code style="background:#f0f0f0;padding:1px 5px;border-radius:3px;font-size:13px;">$1</code>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\\/li>)/gs, '<ul style="padding-left:18px;">$1</ul>')
    .replace(/\\n/g, '<br>');
}

// ── 学习报告 ────────────────────────────────────────────────────
async function viewReport(forceRefresh) {
  if (!currentPlanId) return;
  showPage('report');
  setTopbar('学习报告', '');
  const el = document.getElementById('reportContent');
  const url = '/plans/' + currentPlanId + '/report' + (forceRefresh ? '?refresh=true' : '');
  el.innerHTML = '<div style="padding:40px;text-align:center;color:#888;font-size:14px;">' +
    (forceRefresh ? '⏳ 正在根据最新进度重新生成报告...' : '⏳ 正在加载学习报告...') + '</div>';

  try {
    const res = await fetch(url);
    const data = await res.json();
    if (data.detail) {
      el.innerHTML = '<div style="padding:40px;text-align:center;"><p style="color:#ff4d4f;">⚠️ ' + escHtml(data.detail) + '</p><button class="lesson-back" style="margin-top:12px;" onclick="showSyllabus(currentPlanId)">← 返回大纲</button></div>';
      return;
    }
    renderReport(data.report, data.generated_at, data.has_update, data.new_submissions, data.from_cache);
  } catch {
    el.innerHTML = '<div style="padding:40px;text-align:center;"><p style="color:#ff4d4f;">⚠️ 报告加载失败，请重试</p><button class="lesson-back" style="margin-top:12px;" onclick="showSyllabus(currentPlanId)">← 返回大纲</button></div>';
  }
}

function renderReport(r, generatedAt, hasUpdate, newSubmissions, fromCache) {
  const el = document.getElementById('reportContent');
  const pct = r.score_pct;
  const ringClass = pct >= 80 ? 'good' : pct >= 60 ? 'ok' : 'bad';

  // 更新提示横幅
  let updateBanner = '';
  if (hasUpdate && fromCache) {
    updateBanner = '<div style="background:#e6f7ff;border:1px solid #91d5ff;border-radius:8px;padding:12px 16px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">' +
      '<span style="font-size:13px;color:#0050b3;">自上次报告后你又完成了 <b>' + newSubmissions + '</b> 个课时的作业，报告数据可能不是最新的</span>' +
      '<div style="display:flex;gap:8px;">' +
        '<button onclick="viewReport(true)" style="padding:5px 16px;border-radius:6px;border:none;background:#1677ff;color:#fff;font-size:13px;font-weight:600;cursor:pointer;">更新报告</button>' +
        '<button onclick="document.getElementById(&quot;updateBanner&quot;).style.display=&quot;none&quot;" style="padding:5px 16px;border-radius:6px;border:1px solid #d9d9d9;background:#fff;color:#666;font-size:13px;cursor:pointer;">暂不更新</button>' +
      '</div></div>';
    updateBanner = '<div id="updateBanner">' + updateBanner + '</div>';
  }

  // 缓存来源提示
  let cacheHint = '';
  if (fromCache && !hasUpdate) {
    cacheHint = '<div style="text-align:center;font-size:11px;color:#aaa;margin-top:-8px;margin-bottom:12px;">报告生成于 ' + escHtml(generatedAt) + '，数据已是最新</div>';
  } else if (fromCache && hasUpdate) {
    cacheHint = '<div style="text-align:center;font-size:11px;color:#aaa;margin-top:-8px;margin-bottom:12px;">报告生成于 ' + escHtml(generatedAt) + '</div>';
  }

  const lessonsHtml = r.lessons.map(l => `
    <div class="report-lesson-row ${l.passed ? 'passed' : 'failed'}">
      <div class="report-lesson-idx">${l.lesson_index}</div>
      <div class="report-lesson-title">${escHtml(l.title)}</div>
      <div class="report-lesson-score">${l.score}/${l.max_score}</div>
    </div>`).join('');

  const weakHtml = r.weak_points && r.weak_points.length
    ? r.weak_points.map(w => '<span class="report-tag weak">' + escHtml(w) + '</span>').join('')
    : '<span style="color:#aaa;font-size:13px;">暂无</span>';

  const strongHtml = r.strengths && r.strengths.length
    ? r.strengths.map(s => '<span class="report-tag strong">' + escHtml(s) + '</span>').join('')
    : '<span style="color:#aaa;font-size:13px;">暂无</span>';

  const suggestionsHtml = r.suggestions.map(s =>
    '<div class="report-suggestion">💡 ' + escHtml(s) + '</div>'
  ).join('');

  el.innerHTML = `
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
      <button class="lesson-back" onclick="showSyllabus(currentPlanId)">←</button>
      <div style="font-size:17px;font-weight:700;">📊 学习报告</div>
    </div>

    ${updateBanner}
    ${cacheHint}

    <div class="report-header">
      <h2>${escHtml(r.plan_title)}</h2>
      <div class="report-score-ring ${ringClass}">${pct}%</div>
      <div class="report-stats">
        <div class="report-stat">
          <div class="report-stat-num">${r.completed}/${r.total_lessons}</div>
          <div class="report-stat-label">已完成作业</div>
        </div>
        <div class="report-stat">
          <div class="report-stat-num">${r.passed}/${r.total_lessons}</div>
          <div class="report-stat-label">已通过</div>
        </div>
        <div class="report-stat">
          <div class="report-stat-num">${r.total_score}/${r.total_max}</div>
          <div class="report-stat-label">总得分</div>
        </div>
      </div>
    </div>

    <div class="report-section">
      <div class="report-section-title">📋 各课时成绩</div>
      ${lessonsHtml}
    </div>

    <div class="report-section">
      <div class="report-section-title">⚠️ 薄弱知识点</div>
      <div class="report-tags">${weakHtml}</div>
    </div>

    <div class="report-section">
      <div class="report-section-title">✅ 掌握较好</div>
      <div class="report-tags">${strongHtml}</div>
    </div>

    <div class="report-section">
      <div class="report-section-title">💡 学习建议</div>
      ${suggestionsHtml}
    </div>

    <div class="report-section">
      <div class="report-section-title">📝 整体评价</div>
      <div class="report-summary">${escHtml(r.summary)}</div>
    </div>`;
}

// ── 作业系统 ────────────────────────────────────────────────────
let currentHomework = null;
let currentLessonIndex = null;

async function checkExistingHomework(lessonIndex) {
  try {
    const res = await fetch('/plans/' + currentPlanId + '/lessons/' + lessonIndex + '/homework');
    if (res.ok) {
      const data = await res.json();
      currentHomework = data.homework;
      currentLessonIndex = lessonIndex;
      const btn = document.getElementById('hwGenBtn');
      btn.textContent = '📝 查看/做作业';
      btn.onclick = () => renderHomeworkQuiz(currentHomework);
      // 也检查是否有提交结果
      try {
        const rr = await fetch('/plans/' + currentPlanId + '/lessons/' + lessonIndex + '/homework/result');
        if (rr.ok) {
          const result = await rr.json();
          renderHomeworkQuiz(currentHomework, result.result);
        }
      } catch {}
    }
  } catch {}
}

async function generateHomework(lessonIndex) {
  const btn = document.getElementById('hwGenBtn');
  btn.disabled = true;
  btn.textContent = '⏳ 正在生成作业题目...';
  currentLessonIndex = lessonIndex;

  try {
    const res = await fetch('/plans/' + currentPlanId + '/lessons/' + lessonIndex + '/homework/generate', { method: 'POST' });
    const data = await res.json();
    if (data.detail) {
      btn.textContent = '⚠️ ' + data.detail;
      setTimeout(() => { btn.textContent = '📝 生成本课作业'; btn.disabled = false; }, 3000);
      return;
    }
    currentHomework = data;
    renderHomeworkQuiz(data);
  } catch {
    btn.textContent = '⚠️ 生成失败，请重试';
    setTimeout(() => { btn.textContent = '📝 生成本课作业'; btn.disabled = false; }, 3000);
  }
}

function renderHomeworkQuiz(hw, result) {
  const area = document.getElementById('homeworkArea');
  const isGraded = !!result;

  let bannerHtml = '';
  if (isGraded) {
    const passed = result.passed;
    bannerHtml = `
      <div class="hw-result-banner ${passed ? 'passed' : 'failed'}">
        <div class="hw-score">${result.total_score}/${result.max_score}</div>
        <div class="hw-result-info">
          <div class="hw-result-status">${passed ? '🎉 恭喜通过！' : '💪 继续加油！'}</div>
          <div style="font-size:13px;color:#888;margin-top:2px;">${passed ? '你已掌握本课核心知识点' : '建议复习后重新作答'}</div>
        </div>
      </div>
      <div style="font-size:14px;line-height:1.8;color:#333;margin-bottom:16px;padding:12px 16px;background:#f8faff;border-radius:8px;">
        ${escHtml(result.summary)}
      </div>
      ${result.weak_points && result.weak_points.length ? '<div class="hw-weak-points">' + result.weak_points.map(w => '<span class="hw-weak-tag">⚠️ ' + escHtml(w) + '</span>').join('') + '</div>' : ''}
    `;
  }

  // 构建结果映射
  const gradeMap = {};
  if (isGraded && result.items) {
    result.items.forEach(item => { gradeMap[item.index] = item; });
  }

  const questionsHtml = hw.questions.map(q => {
    const g = gradeMap[q.index];
    const qClass = g ? (g.is_correct ? 'correct' : 'wrong') : '';

    let answerHtml = '';
    if (q.type === 'choice') {
      answerHtml = '<div class="hw-options">' + q.options.map((opt, i) => {
        const letter = String.fromCharCode(65 + i);
        const selected = g && g.user_answer === letter ? 'selected' : '';
        return `<div class="hw-option ${selected} ${isGraded ? '' : ''}" data-q="${q.index}" data-val="${letter}"
                     ${isGraded ? '' : 'onclick="selectOption(this)"'}>
          <div class="hw-option-radio"></div>
          <span>${escHtml(opt)}</span>
        </div>`;
      }).join('') + '</div>';
    } else {
      const val = g ? escHtml(g.user_answer) : '';
      answerHtml = `<textarea class="hw-textarea" data-q="${q.index}" placeholder="${q.type === 'coding' ? '请输入代码...' : '请输入你的答案...'}" ${isGraded ? 'disabled' : ''}>${val}</textarea>`;
    }

    let feedbackHtml = '';
    if (g) {
      feedbackHtml = `
        <div class="hw-feedback" style="margin-top:10px;">
          <span style="font-weight:600;color:${g.is_correct ? '#389e0d' : '#cf1322'};">${g.is_correct ? '✅ 正确' : '❌ 错误'}（${g.score}/${q.points} 分）</span><br>
          ${escHtml(g.feedback)}
        </div>`;
    }

    return `
      <div class="hw-question ${qClass}">
        <div class="hw-q-header">
          <div class="hw-q-num">${q.index}</div>
          <span class="hw-q-type">${q.type === 'choice' ? '选择题' : q.type === 'coding' ? '编程题' : '开放题'}</span>
          <span class="hw-q-points">${q.points} 分</span>
        </div>
        <div class="hw-q-text">${escHtml(q.question)}</div>
        ${answerHtml}
        ${feedbackHtml}
      </div>`;
  }).join('');

  const submitBar = isGraded
    ? `<div class="hw-submit-bar">
        <button class="hw-submit-btn" onclick="retryHomework()">🔄 重新作答</button>
       </div>`
    : `<div class="hw-submit-bar">
        <button class="hw-submit-btn" id="hwSubmitBtn" onclick="submitHomework()">📮 提交作业</button>
        <span style="font-size:12px;color:#aaa;">共 ${hw.total_points} 分</span>
       </div>`;

  area.innerHTML = `
    <div class="homework-title">📝 ${escHtml(hw.title)}</div>
    ${bannerHtml}
    ${questionsHtml}
    ${submitBar}`;
}

function selectOption(el) {
  const qIdx = el.dataset.q;
  document.querySelectorAll('.hw-option[data-q="' + qIdx + '"]').forEach(o => o.classList.remove('selected'));
  el.classList.add('selected');
}

function retryHomework() {
  if (currentHomework) renderHomeworkQuiz(currentHomework);
}

async function submitHomework() {
  if (!currentHomework || !currentPlanId || !currentLessonIndex) return;

  const answers = [];
  currentHomework.questions.forEach(q => {
    if (q.type === 'choice') {
      const sel = document.querySelector('.hw-option.selected[data-q="' + q.index + '"]');
      answers.push({ index: q.index, user_answer: sel ? sel.dataset.val : '' });
    } else {
      const ta = document.querySelector('.hw-textarea[data-q="' + q.index + '"]');
      answers.push({ index: q.index, user_answer: ta ? ta.value.trim() : '' });
    }
  });

  // 检查是否有未作答的题
  const unanswered = answers.filter(a => !a.user_answer);
  if (unanswered.length > 0) {
    if (!confirm('还有 ' + unanswered.length + ' 道题未作答，确定要提交吗？')) return;
  }

  const btn = document.getElementById('hwSubmitBtn');
  btn.disabled = true;
  btn.textContent = '⏳ 正在批改...';

  try {
    const res = await fetch('/plans/' + currentPlanId + '/lessons/' + currentLessonIndex + '/homework/submit', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ answers: answers }),
    });
    const data = await res.json();
    if (data.detail) {
      btn.textContent = '⚠️ ' + data.detail;
      setTimeout(() => { btn.textContent = '📮 提交作业'; btn.disabled = false; }, 3000);
      return;
    }
    renderHomeworkQuiz(currentHomework, data);
  } catch {
    btn.textContent = '⚠️ 提交失败，请重试';
    setTimeout(() => { btn.textContent = '📮 提交作业'; btn.disabled = false; }, 3000);
  }
}

// ── 资料库 ──────────────────────────────────────────────────────
async function loadBookOptions() {
  const sel = document.getElementById('fieldBook');
  const current = sel.value;
  sel.innerHTML = '<option value="">不使用参考书籍</option>';
  try {
    const resp = await fetch('/books');
    const books = await resp.json();
    books.forEach(b => {
      const opt = document.createElement('option');
      opt.value = b.id;
      opt.textContent = b.title + ' (' + b.file_type.toUpperCase() + ')';
      sel.appendChild(opt);
    });
    if (current) sel.value = current;
  } catch(e) { /* ignore */ }
}

function showBooks() {
  showPage('books');
  setTopbar('学习资料库', '上传学习资料，增强 AI 教学效果');
  loadBooks();
}

async function loadBooks() {
  try {
    const resp = await fetch('/books');
    const books = await resp.json();
    const list = document.getElementById('bookList');
    if (!books.length) {
      list.innerHTML = '<div class="books-empty">暂无上传资料，上传文件后 AI 将基于资料内容辅助教学</div>';
      return;
    }
    list.innerHTML = books.map(b => {
      const iconMap = {txt: '📄', md: '📝', epub: '📖'};
      const icon = iconMap[b.file_type] || '📄';
      const size = b.file_size < 1024 ? b.file_size + ' B'
                 : b.file_size < 1048576 ? (b.file_size/1024).toFixed(1) + ' KB'
                 : (b.file_size/1048576).toFixed(1) + ' MB';
      return '<div class="book-card">' +
        '<div class="book-icon ' + b.file_type + '">' + icon + '</div>' +
        '<div class="book-info">' +
          '<div class="book-title">' + escHtml(b.title) + '</div>' +
          '<div class="book-meta">' + b.file_type.toUpperCase() + ' · ' + size + ' · ' + b.chunk_count + ' 个片段 · ' + b.created_at + '</div>' +
        '</div>' +
        '<button class="book-delete" onclick="deleteBook(' + b.id + ')">删除</button>' +
      '</div>';
    }).join('');
  } catch(e) {
    console.error('loadBooks error:', e);
  }
}

async function deleteBook(id) {
  if (!confirm('确定要删除这本资料吗？同时会从知识库中移除。')) return;
  try {
    await fetch('/books/' + id, {method: 'DELETE'});
    loadBooks();
  } catch(e) {
    alert('删除失败：' + e.message);
  }
}

// 文件上传
(function initUpload() {
  const area = document.getElementById('uploadArea');
  const input = document.getElementById('fileInput');

  // 拖拽支持
  area.addEventListener('dragover', e => { e.preventDefault(); area.classList.add('dragging'); });
  area.addEventListener('dragleave', () => area.classList.remove('dragging'));
  area.addEventListener('drop', e => {
    e.preventDefault();
    area.classList.remove('dragging');
    if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
  });

  input.addEventListener('change', () => {
    if (input.files.length) uploadFile(input.files[0]);
    input.value = '';
  });
})();

async function uploadFile(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['txt', 'md', 'epub'].includes(ext)) {
    alert('不支持的文件格式，仅支持 txt / md / epub');
    return;
  }
  if (file.size > 50 * 1024 * 1024) {
    alert('文件过大，最大支持 50MB');
    return;
  }

  const progress = document.getElementById('uploadProgress');
  const bar = document.getElementById('uploadBar');
  const status = document.getElementById('uploadStatus');
  progress.style.display = 'block';
  bar.style.width = '30%';
  status.textContent = '正在上传 ' + file.name + '…';

  const form = new FormData();
  form.append('file', file);

  try {
    bar.style.width = '60%';
    status.textContent = '正在解析并存入知识库…';
    const resp = await fetch('/books/upload', { method: 'POST', body: form });
    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || '上传失败');
    }
    const data = await resp.json();
    bar.style.width = '100%';
    status.textContent = '上传成功！已解析 ' + data.chunk_count + ' 个知识片段';
    setTimeout(() => { progress.style.display = 'none'; bar.style.width = '0%'; }, 2000);
    loadBooks();
  } catch(e) {
    bar.style.width = '0%';
    status.textContent = '上传失败：' + e.message;
    setTimeout(() => { progress.style.display = 'none'; }, 3000);
  }
}

// ── 工具函数 ──────────────────────────────────────────────────
function escHtml(str) {
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
</script>
</body>
</html>
"""

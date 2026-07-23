---
title: "你以為你會用 AI？從跟 ChatGPT 聊天到 AI Agent 的五個階段，你在哪一階？"
date: 2026-07-19
slug: "2026-07-19-ai-interface-evolution"
cover:
  image: "images/TQ3SgrW9lkM-unsplash.jpg"
  alt: "a yellow letter sitting on top of a black floor"
  credit:
    photographer: "Jackson Sophat"
    photographer_url: "https://unsplash.com/@jacksonsophat"
    photo_url: "https://unsplash.com/photos/a-yellow-letter-sitting-on-top-of-a-black-floor-TQ3SgrW9lkM"
images: ["images/TQ3SgrW9lkM-unsplash.jpg", "images/chat-gpt.png", "images/chat-ms-365-copilot.png", "images/vscode.png", "images/github-copilot-desktop-app.jpg", "images/claude-code-cli.png"]
categories: ["澳洲職場"]
tags: ["AI", "Claude", "Gemini", "ChatGPT", "Copilot", "軟體工程師"]
---

最近常跟朋友、同事聊 AI，才發現大家講的「ChatGPT」、「Claude」、「Gemini」、「Copilot」，其實指的可能完全不是同一件事。

有人講的是 Web Chat 網頁聊天介面（打開瀏覽器就能聊天的版本），有人講的是 IDE（直接整合在 VS Code、Cursor 等開發工具裡），有人講的是 CLI（在 Terminal 裡用指令操作）。

明明都叫 Claude、都叫 ChatGPT，使用體驗卻完全是不同世界。

所以我後來除了聊模型本身，也會先確認對方是從哪個「入口」使用，不然常常都是在雞同鴨講🤣

> 很多工程師說自己在用 Claude，其實指的是 CLI（Command Line Interface），也就是在 Terminal 用文字指令跟 AI 協作；另一群人則是在 IDE（Integrated Development Environment，整合式開發環境），例如 VS Code 或 Cursor 裡，直接讓 AI 幫忙寫程式、修改檔案。跟一般人說「我跟 Claude 聊天」，其實是不同的概念。

我後來發現，AI 其實可以拆成三個層次：

1. 模型（Model）：AI 工具背後的大語言模型，例如 GPT-5.5、Claude Opus、Gemini 3.5，也就是 AI 的「大腦」。
2. 入口（Interface）：跟 AI 互動的介面，例如 Web Chat、IDE、CLI，也就是你跟 AI 溝通的方式。
3. 產品（Product）：把 1 跟 2 結合起來，包裝成大家使用的服務，也算是 AI 工作的統稱，例如 Codex、Claude Code、GitHub Copilot、Cursor。

很多人會把這三層混在一起，所以討論 AI 時，常常其實是在講不同東西。

為了幫大家進一步釐清概念，我先用我自己的方式，把 AI 工具依照一般人的使用歷程分成幾個階段。

每個階段我會給大家代表性的工具，他們各自的特點，再加上我個人的使用心得。

---

## Level 1：Web Chat (網頁聊天介面)，所有人的 AI 起點

{{< figure src="images/chat-gpt.png" alt="ChatGPT 網頁聊天介面" >}}

代表產品

* ChatGPT Chat
* Gemini Chat
* Claude Chat

我想跟 ChatGPT 聊天應該是大多數人跟 AI 相處的起點XD

這個階段的典型用途大概是：問問題、聊天、改 email、摘要文章等等，單純跟語言文字相關的任務。

**EC 使用心得**

隨著越來越多的大語言模型服務商出現，目前呈現百花齊放的階段，但我認為 ChatGPT 在聊天上跟提供情緒支持上還是有其優勢XD

網頁聊天介面是目前最多人體驗 AI 的方式。但如果一直停留在這裡，很容易得到一個結論：「AI 不錯用，但好像沒有大家說得那麼神。」

因為你只是把 AI 當搜尋引擎升級版而已XDDD

**Level 1： 大概 90% 的一般使用者都是停在這裡。**

---

## Level 2：企業版 AI，公司開始花錢買 AI 的第一步

{{< figure src="images/chat-ms-365-copilot.png" alt="M365 Copilot 網頁聊天介面" >}}

代表產品

* Microsoft 365 Copilot

整合了多數微軟的服務，例如 Outlook、Teams、Word、PowerPoint、SharePoint 等等。

**EC 使用心得**

微軟生態圈真的很強，也真的什麼都想整合。但不知道為什麼，每個地方的 Copilot 都有一點讓人無言以對，總是給人一種：「好像快成功了，但最後一步永遠失敗」的感覺🤣

例如：

- 幫我直接修改 Outlook Email -> 改完了，但沒有辦法直接更新信件內文，失敗！

- 幫我根據某某主題產生 PowerPoint -> 做出來了，但顏色跟樣式根本不對，失敗！

Microsoft Copilot Web chat 的回答也是常常差強人意

每次都用到我很生氣，覺得浪費我的時間，還不如我自己做更快🤣

**Level 2： 大概 90% 的一般企業使用者會停在這裡。**

---

## Level 3：IDE，真正開始感受到 AI 威力


{{< figure src="images/vscode.png" alt="VS Code + GitHub Copilot 介面" >}}


代表工具：

* Cursor
* VS Code + GitHub Copilot
* VS Code + Claude Extension

這時候 AI 不再只是聊天，而是：

* 程式碼編輯: code generation, code refactoring, debug, test generation
* 畫各式流程圖、data flow charts、wireframes
* 專案架構與設計


**EC 使用心得**

我自己大概停留在這個階段半年，很常開不同對話視窗，請 AI 跟我一起 brainstorm、做 solution design，來回討論個幾次，確定方案之後，就開始執行，感覺就跟另一位工程師一起工作一樣。

也是我開始真正覺得：「喔，AI 真的開始改變我的工作方式了」的時刻。

**Level 3： 剛剛接觸 AI 的工程師大概在這裡。**

---

## Level 4：CLI/Desktop App，AI 不只是寫程式，而是開始執行專案

如果你已經到了這一步，先說聲「恭喜」，因為你已經開始指揮 AI，而不是單純使用 AI。

除了一般操作 Terminal、執行 Commands，你的工作流程開始出現多個 Agents、啟用多個 sub-agents，fan out to multiple workflows、parallel tasks、自動化 workflows 等等。

{{< figure src="images/github-copilot-desktop-app.jpg" alt="GitHub Copilot Desktop App 介面" >}}
{{< figure src="images/claude-code-cli.png" alt="Claude Code CLI 介面" >}}

代表：

* Claude Code CLI
* GitHub Copilot CLI
* Claude Code Desktop
* Codex Desktop App
* GitHub Copilot Desktop App



**EC 使用心得**

第一次看到同事一次開十幾個 agents，我當下的反應是：「等等，你平常工作到底有多難？🤣」

這個階段跟 IDE 最大差別是「Agent 感」開始出現了。

AI 的效能開始成倍數成長，使用起來已經不像是我在跟一位工程師一起工作，而是我一個人就在指揮一群 AI 大軍(軟體工程師、測試工程師、UX/UI 設計師、Business Analyst 等等)，跟我一起衝鋒陷陣，我負責指揮，他們負責完成。

很多時候，比較簡單的任務，AI agents 甚至可以直接跑完整段流程 (end to end workflow)，完全不需要我給過多指示。

**Level 4： 擁有進階 AI 工具跟知識的工程師大概在這裡。**

---

## Level 5：自己打造 AI Agents/Harness

然後就是我那些很誇張的同事，他們已經不是在使用 AI，而是自己做 AI。

例如：

* 自建 AI Harness
* 自己寫 Agent Framework
* 自己部署 Local Model
* 自己 Train Model

第一次聽到同事說：「我昨天在家 train local model。」

我還以為他在 Amazon Bedrock 上面跑模型，結果不是。

是他自己組了一台電腦，買了超貴的顯卡，然後開始跑不連外網 (public internet)，只連他自己的 home network & home server room 的本地模型！

我問他：「所以你到底在訓練什麼模型？」

他：「分析我家的狗！」

原來他是透過家用攝影機，做影像辨識，分析狗狗每天的行為模式。

我真的笑死！！！

---

## 結語：真正決定 AI 體驗的，可能不是模型

最近大家都在討論：

* GPT 比 Claude 強嗎？
* Gemini 追上了嗎？
* Copilot 值得訂閱嗎？

但我越用越覺得，真正決定 AI 體驗的，很多時候不是模型本身，而是：

* 你從哪個入口開始使用它？
* 它能不能融入你的工作流程？
* 它能不能真正幫你完成事情，而不是只是回答問題？

大語言模型會持續進步，AI 模型排行榜也會持續變動。今天第一名的模型，明天可能就被另一個模型超越。

但使用者真正留下來的，通常不是某個 benchmark（基準測試）上的分數，而是一套能穩定產生價值的工作流程。

所以與其問「哪個 AI 最強」，也許更值得問的是：「哪個 AI 模型＋AI 介面最適合我的工作方式？」

畢竟，最強的工具不是能力最高的那一個，而是你真正會使用、並且能持續幫助你完成事情的那一個。

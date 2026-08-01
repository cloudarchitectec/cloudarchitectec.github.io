---
title: "AI 沒有取代工程師，但正在重新定義什麼叫做「好的工程師」"

date: 2026-07-04
slug: "2026-07-04-soft-skills-in-ai-era"
cover:
  image: "images/zwd435-ewb4-unsplash.jpg"
  alt: "坐在長椅上看著筆電的人形機器人"
  credit:
    photographer: "Andrea De Santis"
    photographer_url: "https://unsplash.com/@santesson89"
    photo_url: "https://unsplash.com/photos/black-and-white-robot-toy-on-red-wooden-table-zwd435-ewb4"
images: ["images/zwd435-ewb4-unsplash.jpg"]
categories: ["澳洲職場"]
tags: ["AI", "軟實力", "軟體工程師", "GitHub Copilot"]
---

我們公司使用 Microsoft Copilot 已經一陣子了(很難用，不要問🤣)，前陣子更是全面導入企業版 GitHub Copilot。不是那種「大家體驗看看」的等級，而是真正投入正式日常工作流程。

公司提供的是企業授權，可以直接使用 GPT 5.4、Claude Sonnet 4.6、Opus 4.8 等各種當前最先進的模型，AI credits 多到滿出來XD (每個人的額度都相當可觀)

我們團隊也開始大量探索 AI Agent 的工作模式，像是 MCP、Agent Skills、GitHub Agentic Workflows 等，希望把 AI 真正整合進軟體開發流程，而不是只是拿來寫幾段程式碼。

說真的，經過一段時間的練習與實戰應用之後，生產力的提升真的很有感。我也開始覺得：好，AI 時代是真的來了！

一直到某天下午，我注意到一件很有趣的小事。

有位同事突然說：

> 「我的 GitHub Copilot credits 用完了。」

原本大家只是笑笑，想說再跟公司申請更多 AI credits 就好。不過因為是大型企業，申請流程沒有想像中快速。

接下來的幾天我發現，那個同事幾乎沒有什麼進度。

不是因為他不會寫程式。相反地，他一直都是我認為非常優秀的工程師，程式基礎扎實，系統架構與設計也很有自己的想法。

真正卡住的，是他的日常工作流程。沒有了 AI，他似乎失去了所有的「超能力」，變成了無能為力的「普通人」。

那一刻，我突然開始思考一個問題：我們是不是已經在不知不覺中把 AI 放到了工作流程的核心，取代了我們的大腦？

---

## AI 已經不只是「工具」了

如果把時間拉回幾年前，大部分工程師的工作流程可能長這樣：

定義需求 → 規劃架構 → 寫程式 → Google/Stack Overflow/Debug → 寫程式 → 實現功能。

現在呢？

至少我的日常，越來越像是：

提出問題 → Agent 分析需求 → Agent 規劃架構（我核實，提出問題與建議，與 Agent 來回修改，定案） → Agent 產生程式 → Agent Review → Human Review (大方向) → 修正 → 再交給 Agent。

以前 AI 是工具，現在 AI 更像是無所不在的 Pair Programmer。工作內容沒有改變，但工作方式，早就完全不一樣了。

AI 已經被內化進整個流程之中，一旦把 AI Agent 抽離，整條流水線就突然斷掉了！？

---

## 研究證明，AI 確實能有效提高生產力

雖然目前還沒有很多 AI 跟生產力的研究數據，這些研究可能也沒有很有代表性，但或許我們可以從中觀察到一些現象。

Microsoft Research 做過一個 RCT 實驗，讓工程師完成同一個 HTTP Server 任務。沒有 Copilot 平均要 160 分鐘，有 Copilot 的只要 71 分鐘，完成速度快了 55.8%。[1]

Fortune 100 企業的大型實驗，追蹤了將近 5000 名工程師，使用 Copilot 後完成工作量提升了 26%。[2]

MIT 的一項研究也顯示，知識工作者用 AI 後工作時間縮短了四成，品質還提升了 18%。[3]

數字很漂亮，不容否認！有趣的是，受益最大的都是經驗較少的工程師。

---

## 越強的人，AI 對他的幫助越有限？

NBER 針對五千多位客服人員的研究發現，AI 讓整體生產力提升約 14%，其中新人的提升高達 34%，但是資深人員幾乎沒有明顯變化。[4]

這讓我想到一句很有意思的話：

AI 正在把資深人員的經驗，包裝成每個人都可以隨時呼叫的工具模組。以前需要累積好幾年的經驗，現在新人也能快速得到類似的結果（是嗎？畢竟品質一向就是最難以評估跟量化的指標🤣）。

這對整個產業而言，是一件好事，但它也帶來另一個問題：如果 AI 已經把「寫程式」這件事變得越來越容易，那資深工程師真正的價值，還剩下什麼？

## 寫程式變快了，不代表開發變快了

當然，也不是所有研究都這麼樂觀。

2025 年 METR 研究了一群資深開源工程師，結果相當出乎意料。工程師普遍認為自己因為 AI 快了約 24%，但實際測量卻發現，整體反而慢了約 19%。[5]

這原因並不難理解：因為有些工程師實際上花了更多時間驗證 AI 的答案、修正 AI 引入的新問題、重新理解 AI 為什麼會這樣設計。俗稱：幫 AI 擦屁股XD

另一份研究也指出，Copilot 雖然提升了個人寫程式的速度，但團隊整體的整合時間反而增加。[6]

看到這些研究，我反而很有共鳴。因為大型企業真正花時間的，從來不是把一個功能或是小工具寫出來。真正困難的，是讓數個系統一起正常運作。而這件事，目前 AI 還沒有辦法完全解決。

---

## AI 時代，好的工程師正在重新被定義

說了這麼多背景，回到最核心的問題：如果 AI 已經改變了工作流程，那工程師真正需要進化的技能，還是「寫更好的程式」嗎？

我覺得不是，或者說，那只是其中一部分。

我觀察下來，AI 時代真正稀缺的能力，其實是以下這幾件事：

- 「Problem Solving (問題拆解能力)」 

AI 很少因為程式寫不出來而卡關。更多時候，是因為我們人類沒有把問題描述清楚。

需求拆解得越好，AI 的回答通常就越好。

很多人以為 Prompt Engineering 是複製貼上修改 prompts。我反而覺得，它更像需求分析，很多時候，沒有一定的經驗累積，很難一次就給出正確的指示，或是找到 AI 的盲點。（雖然隨著大語言模型越來越進化，有一派的說法是現在的前端模型已經不需要過多的 prompting，因為他們已經聰明到可以自己摸索加理解了）


- 「Context Management (背景知識管理)」 

另一個關鍵能力是：知道要給 AI 什麼背景知識，並且知道哪些東西不要給。太多無效的 context 會讓模型產生混淆，太少又讓它答非所問。如何提供剛剛好的資訊，開始變成一項新的基本功。

- 「AI Orchestration (AI 多工規劃統籌)」 

以前，我們習慣靠自己＋程式碼完成所有事情。現在則更像是在管理一群能力很強、速度很快，但偶爾會一本正經胡說八道又過度自信的實習生XD

你要分配工作、定義標準、檢查產出、決定哪些可以採用，哪些需要推翻重來。

工程師開始更像管理核心，而不是一個單純透過程式編碼來達成目的的人。

- 「Critical Thinking (批判性思考)」 

AI 唬爛或是產生幻覺的時候，你要能看出來。

這聽起來很基本，但真的在用的人都知道，AI 有時候會生成一些格式很漂亮的垃圾，或是捏造證據，如果不夠熟悉那個領域，或沒有細心覺察，非常容易被騙過去。

- 「Cross-system Thinking (跨系統性思考)」 

這是目前 AI 最弱的地方。

它可以很好地處理單一功能，甚至是單一系統，但要理解整個企業系統的設計邏輯、不同系統、平台、應用程式之間的依存關係、某個改動的連鎖效應，還是有一定的難度。

---

## 最後，我想所有工程師都要問自己一個問題

如果明天 Copilot 掛掉、Claude 掛掉、credits 用完，你還能不能繼續完成現有的工作？

如果你的答案是：「可以，只是比較慢一點」，那 AI 對你來說是槓桿，你在用它放大自己的能力。

如果你的答案是：「我不知道從哪開始」，那 AI 已經變成支持你的拐杖了，現在沒有 AI，你突然連怎麼走路都忘了。

同事的故事告訴我：有好用的工具很棒，知道要如何善用工具也很棒，但我們不應該因為太過依賴工具，而喪失了我們最核心的專業能力。

或許 AI 真正改變的，從來不是工程師會不會被取代，而是它正在重新定義，什麼叫做一位好的工程師。

你最近也會在生活或工作上使用 AI 嗎？歡迎留言跟我分享你的經驗！

---

## 文中提到的研究

1. Peng, Kalliamvakou, Cihon & Demirer (2023), [*The Impact of AI on Developer Productivity: Evidence from GitHub Copilot*](https://arxiv.org/abs/2302.06590)
2. Cui, Demirer, Jaffe, Musolff, Peng & Salz (2024), [*The Effects of Generative AI on High-Skilled Work: Evidence from Three Field Experiments with Software Developers*](https://economics.mit.edu/sites/default/files/inline-files/draft_copilot_experiments.pdf)
3. Noy & Zhang (2023), [*Experimental Evidence on the Productivity Effects of Generative Artificial Intelligence*](https://economics.mit.edu/sites/default/files/inline-files/Noy_Zhang_1.pdf)
4. Brynjolfsson, Li & Raymond (2023), [*Generative AI at Work*](https://www.nber.org/papers/w31161)
5. METR (2025), [*Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity*](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/)
6. Song, Agarwal & Wen (2024), [*The Impact of Generative AI on Collaborative Open-Source Software Development: Evidence from GitHub Copilot*](https://arxiv.org/abs/2410.02091)

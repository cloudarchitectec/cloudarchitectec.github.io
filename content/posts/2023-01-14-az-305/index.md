---
title: "微軟 Azure 雲端證照: AZ-305 Azure Solutions Architect Expert  證照考試心得"
date: 2023-01-14
slug: "2023-01-14-az-305"
image: "images/medium-1*KvQiCG--vyYalkrYgxe2Gg.png.jpg"
images: ['images/medium-1*KvQiCG--vyYalkrYgxe2Gg.png.jpg']
categories: ["海外職場"]
tags: ["雲端證照"]
---

![Exam badge of AZ Solutions Architect Expert](images/medium-1*KvQiCG--vyYalkrYgxe2Gg.png.jpg)

*Microsoft Certified Azure Solution Architect Expert*

* * *

**考試日期：2023.01.02**

2023 年的第二天，我通過了 AZ-305 Designing Microsoft Azure Infrastructure Solutions 的考試，加上 11 月通過的 AZ-104 Azure Administrator Associate，成功獲得了 Microsoft Certified Azure Solutions Architect Expert 這張專家級證照，算是為了新的一年打下良好的基礎!

今天我要來分享我的考試心得以及準備過程!

### 考場選擇: 考試中心或是在家考試

AZ-305 是我第九張雲端證照，以前還住在雪梨時，我喜歡直接去考試中心考試，因為考場會有筆跟紙讓考生可以做筆記。如果中途想去上廁所，也可以在跟監考人員報備後前往。但後來住在坎培拉跟布里斯本郊區，離最近的考試中心總是要好幾十公里或是好幾百公里遠，所以我也就習慣了在家考試的模式。

在家考試的好處是時間比較彈性，24小時都可以進行考試。壞處就是電腦設備必須通過一連串的系統跟網路測試(如果網路連線不穩，可能考到一半就會無法繼續XD)，並且考試過程中需要全程開著鏡頭方便監考官查看(全程錄影)、沒有辦法手寫筆記、不能去廁所，也不能喝水，一旦有任何人出現在你的房間考試則當場作廢。

在家考試的話，考生可以在測驗時間開始前的半小時登入系統，考生需要用手機當場自拍一張、拍下身分證件與房間的前後左右共六張照片，供監考官查核。等監考官驗證過你的身分跟四周環境後，即可開始考試 。

### 考試當天

以往我總是在系統開放的那一刻就登入系統，通常等我做完身分驗證，5 分鐘以內就可以開始考試。這一次不知道為什麼我照片上傳到一半失敗，只好重新開始驗證過程。不過是晚了5分鐘完成手續，這一次我居然排到了 25 號(昏倒)。過了五分鐘後我的排序才前進了到 21 號，我估計可能要等個 20–30分鐘才能進行考試。最後果然如我預料，原定11點考試，我10:30開始登入系統，10:35 完成登入手續，後來整整等了20分鐘，直到10:55才開始考試。等待的過程其實非常難熬，因為一旦登入手續完成，電腦鏡頭就開始全程錄影了，我不能離開座位、也不能喝水或做其他事，只能看著電腦螢幕發呆。

AZ-305的考試時長是 120 分鐘，我花了30分鐘寫完 46 題 (這次很幸運只有 道 case study題)，然後花了30 分鐘檢查，然後我就交卷了。交卷完很幸運地以 710分通過 (通過標準是 700/1000)，也就是說我大概只要再錯一題，就直接掰掰了XD

我覺得自己非常幸運!!! 雖然這是我目前的雲端證照(六張 AWS、三張 Azure) 裡面最低分的一張，不過我目前為止還是保持著每張證照只考一次就通過的紀錄XD 直接公開分數也是想要跟大家說，有時候考證照也不是那麼容易，如果準備得不充分，或是選擇了錯誤的讀書計畫跟策略，也可能會有失敗的風險哈哈

### 準備心得與反思

這次我仍然選用了 A Cloud Guru (ACG) 的 [AZ-305: Designing Microsoft Azure Infrastructure Solutions](https://acloudguru.com/course/az-305-designing-microsoft-azure-infrastructure-solutions) 課程，如果有讀過我之前這篇 [微軟 Azure 雲端證照: 只花 40 小時順利通過 AZ-104 Azure Administrator Associate](/posts/2022-11-19-azure-az-104-study/) 的朋友，應該還會記得我上次對於使用 ACG 課程其實不是太滿意。

我這次的確事先嘗試了一下外國網友們大推的微軟官方課程 [AZ-305 Learning Path](https://learn.microsoft.com/en-us/certifications/exams/az-305)

*，但我後來發現這個學習資源基本上就是把各種相關的 Azure官方文件集結在一起。我個人還是比較偏好影音式學習的方式，所以我後來還是花了約兩個月的時間，把 ACG 的課程上完(這次的整體準備時間較長，主要是因為我的工作開始忙了起來，所以中間幾乎找不到時間學習)。*

相信大家看到我的成績之後，會發現我還是對於ACG的課程效果不滿意XDDD

大多數人準備考 AZ-305 時，我相信你們大多數都已經考過 AZ-104 Azure Administrator Associate 了，也就是已經對於 Azure 服務有了一定的知識基礎。我建議你這時候不需要再看其他課程，直接使用 [Exam Topics Microsoft AZ-305 Exam](https://www.examtopics.com/exams/microsoft/az-305/) 來模擬做題。每題作完務必參考網友回答及相關連結，確保自己真的了解該題所問的 domain knowledge 就可以了。基本上這套模擬考題的真實度相當高，我的考試過程中遇到好幾題一模一樣的題目，我非常推薦這個免費資源!

就我個人的考試經驗來說，AZ-305 的考試重點在於 AD (Identity)、Storage (Azure Kubernetes Service)、Networking (尤其是 load balancers 的選擇)，以及 database。大家可以針對這幾個領域加強! 不過由於這個考試是隨機抽題，每個考生的題目跟題目數量都不一定一樣，建議大家還是要盡量做好全方位的準備。

題外話，AZ-104 的考試方向跟 AZ-305的考試方向截然不同，大家千萬不要抱持著同樣的心態去考試XD AZ-104非常重視各種 implementation details，也就是你最好要有 Azure 平台的實際操作經驗，然而 AZ-305 更重視整體的 solution design 跟各個服務之間的關係，完全不考操作細節。

如果大家有什麼 AWS/Azure 證照相關的問題，都歡迎留言。我下次也會再寫一篇 AWS 跟 Azure 兩大雲端證照考試的相關比較，敬請關注!

{{< footer >}}

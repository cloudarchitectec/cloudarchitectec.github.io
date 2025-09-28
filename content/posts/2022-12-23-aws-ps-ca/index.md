---
title: "澳洲亞馬遜 AWS Professional Services Cloud Architect 工作內容分享"
date: 2022-12-23
slug: "2022-12-23-aws-ps-ca"
image: "images/medium-0*SeJpdD8zq08awCIa.jpg"
images: ['images/medium-0*SeJpdD8zq08awCIa.jpg']
categories: ["職涯"]
tags: ["職涯", "AWS"]
---

* * *

### **澳洲亞馬遜 AWS Professional Services Cloud Architect 工作內容分享**

![A man in a suit 穿西裝的男子](images/medium-0*SeJpdD8zq08awCIa.jpg) Photo by [Hunters Race](https://unsplash.com/@huntersrace?utm_source=medium&utm_medium=referral) on [Unsplash](https://unsplash.com?utm_source=medium&utm_medium=referral)

非 Medium 付費會員，請[點此免費閱讀這篇文章](https://medium.com/@cloudarchitectec/aws-professional-services-cloud-architect-%E5%B7%A5%E4%BD%9C%E5%85%A7%E5%AE%B9%E5%88%86%E4%BA%AB-7079361ea84?source=friends_link&sk=7649a888fdc15ce4746f99ca76097249)！當然如果你願意加入 Medium 付費會員來支持創作者，那就更棒囉～感謝你的閱讀！

* * *

今天要來談一談我的上一份工作 Cloud Architect at Amazon Web Services (AWS) Professional Services Team，這是一個很特別的領域! 說實話，在我加入 AWS 前，我從來不知道有這個部門XD 即使是同在 IT 界工作的朋友，也不是每個人都聽說過，所以今天我就來分享一下。

### 什麼是 Professional Services?

Professional Services 簡稱 ProServ，說白了，就是 IT 顧問。想到顧問業，大家心中可能立刻就會浮現「四大」: 勤業眾信 Delottie、安侯建業 KPMG、資誠 PwC、安永 EY，他們除了是四大會計/審計事務所，也是顧問業的龍頭。

那麼 ProServ 平常到底在做什麼呢? 簡單來說，假設今天有一個網路書店，他們本來的 IT 基礎建設都在他們實體的數據中心 (data centre)，例如 on-premises servers and load balancer 等等，但因為網路書店最近業務量漸長，實體的基礎設施已經無法滿足要求。與其添購更多新的硬體，他們想要改往雲端發展 (PS: 其實這就是 Amazon 為什麼後來成立 Amazon Web Services 的真實故事XD)，聽說 AWS 是個很棒的雲端服務平台，然而公司內部的 IT 人員並沒有足夠的雲端技術與知識， 於是他們決定請專業人士來幫他們完成這個從實體伺服器到雲端伺服器的 migration 過程，此時 AWS ProServ 就出場了。

同樣的，這間網路書店也可以找四大 ProServ 來幫他們完成這件事 (而且四大其實還比較便宜XD)。不過還是有很多大型機構 (例如跨國企業、政府部門、大專院校) 會選擇 AWS ProServ，因為我們直屬於 AWS，如果中間遇到什麼問題，我們會有更多 AWS 內部資源可利用。

### **工作內容**

ProServ 的工作內容千奇百怪，因為我們是 by projects 的，也就是說被安排到什麼 projects，我們就要做什麼事XD

舉例來說，我個人曾經幫澳洲某所大學 (澳洲八大之一) 規劃過他們的網路架構跟防火牆規則，也幫澳洲某個科研機構做過內部的資安評估報告 (security assessment)。在我離開 AWS 之前，我參與了澳洲統計局針內部的大數據平台 (data lake) 規劃以及內部工具的更新，協助他們從老舊的企業統計分析軟體轉換成內部網頁工具(web application)，也做過 data engineering & data visualisation。

以上舉的例子在 IT 業界中其實是非常不同的領域，通常不會有人樣樣都專精，但 ProServ 就是必須要有這種遊走在各個不同 IT 領域之間的實力。

### **工作日常**

ProServ 主要的工作內容就是 technical delivery，也就是客戶想要什麼，我們就必須要了解他們的需求、幫他們規劃解決方案，並且幫他們實現。

Senior Cloud Architect 除了要負責帶領技術團隊，常常還需要跟客戶高層開會達成策略 (strategic) 共識。一般的 Cloud Architect 除了執行(寫程式、設定雲端服務)之外，常常也需要跟客戶的 IT 部門或是 developer 部門一起開會、sprint planning、code review 等等，有時候還需要進行一些講座、workshop 來提升客戶 IT 人員的雲端知識與技術。

除此之外，Cloud Architect 對客戶來說以小時計費的。所以一週 40 個小時，我們必須每週回報我們花了多少時間在客戶A身上、多少時間在客戶B身上，多少時間在內部會議跟訓練上。Timesheet 其實是我最不喜歡 ProServ 工作的一點 (這是每個 Cloud Architect 工作表現的硬指標)，因為以客為尊的工作型態，反倒壓縮到我個人學習新技術跟成長的時間。

### **所需技能**

「Cloud Architects 需要會寫程式嗎?」 這可能是我被問過最多的問題，簡單來說寫程式不是必要，但基本上想要完全逃開的話也是不可能的。雖然現在的雲端服務都可以在 GUI console 上架設，不過難免會遇到需要用到 CLI、CDK 或是 SDK 的時候。即使是最近非常流行的 IaC (Infrastructure as Code)，你還是得必須要會寫 CloudFormation (JSON or YAML) 或 Terraform 才行。

更別提現在大家最喜歡用 serverless 服務 (例如 AWS Lamba)，基本上最常見的程式語言就是 Python 或 JavaScript/TypeScript。不過 Cloud Architects 面試不考 coding 也不考 algorithms XD，程式語言只要大概會寫就行 (當然如果你很會寫程式的話，工作效率會大大提升)。

另一個常見的問題則是「我沒有用過 AWS 或 Azure 之類的雲端平台，沒有相關經驗，可以嗎?」答案是完全可以! 當然你有相關經驗是最好，但完全沒有也是沒關係，因為一切都可以進來再學! 面試時我們只會考你 IT 基本知識，例如 networking、database、encryption、application development、security 等等，如果有人有興趣的話，以後可以詳細分享一篇。

那如果以上的技能都不需要，那到底需要什麼呢?

出乎意料的是，除了上述的 IT 基礎知識之外(畢竟 Cloud Architect 還是一個 technical role)，我們最重視的是:

  1. Learning ability: 你有辦法快速學會一個新的技術/雲服務，然後現學現賣把技術傳授給客戶、引導他們跟你一起執行嗎?
  2. Consulting skills: 說到底，Cloud Architect 還是一個技術顧問，你有辦法傾聽客戶的需求、根據他們的要求規劃出解決方案、帶領客戶一起解決疑難雜症、贏得客戶的信任嗎?
  3. Can you be an Amazonian: 亞麻遜一向都以自己獨特的公司文化而自豪，當我們在聘用新員工時，我們也很在乎他們是否跟我們的公司文化契合。有興趣的話，以後也可以專門寫一篇分享 Amazon Leadership Principles interviews。



以上就是 ProServ Cloud Architect 的簡單分享!

* * *



  * 中文部落格: [https://medium.com/@cloudarchitectec](/@cloudarchitectec?source=about_page-------------------------------------)
  * 英文部落格: [https://medium.com/architecting-your-cloud-career](https://medium.com/architecting-your-cloud-career?source=about_page-------------------------------------)
  * Email: [cloudarchitectec@gmail.com](mailto:cloudarchitectec@gmail.com?source=about_page-------------------------------------)
  * 臉書粉絲頁(文章與中文部落格相同): [https://www.facebook.com/cloudarchitectec/](https://www.facebook.com/cloudarchitectec/?source=about_page-------------------------------------)



* * *

**延伸閱讀**

  * [[澳洲職場] 你該轉職嗎? 來自轉職成功者的忠告 (文組轉IT)](https://medium.com/@cloudarchitectec/%E6%BE%B3%E6%B4%B2%E8%81%B7%E5%A0%B4-%E4%BD%A0%E8%A9%B2%E8%BD%89%E8%81%B7%E5%97%8E-%E4%BE%86%E8%87%AA%E8%BD%89%E8%81%B7%E6%88%90%E5%8A%9F%E8%80%85%E7%9A%84%E5%BF%A0%E5%91%8A-%E6%96%87%E7%B5%84%E8%BD%89it-9bb2bb9485ca)
  * [文組轉職澳洲 IT 工程師，我靠 Coding Bootcamp 進了亞馬遜](https://medium.com/@cloudarchitectec/%E6%96%87%E7%B5%84%E8%BD%89%E8%81%B7%E6%BE%B3%E6%B4%B2-it-%E5%B7%A5%E7%A8%8B%E5%B8%AB-%E6%88%91%E9%9D%A0-coding-bootcamp-%E9%80%B2%E4%BA%86%E4%BA%9E%E9%A6%AC%E9%81%9C-30fef5aaa97f)
  * [科技業龍頭 FAANG 的薪資結構解析: 澳洲亞馬遜新鮮人年薪 230 萬台幣!?](https://medium.com/@cloudarchitectec/%E7%A7%91%E6%8A%80%E6%A5%AD%E9%BE%8D%E9%A0%AD-faang-%E7%9A%84%E8%96%AA%E8%B3%87%E7%B5%90%E6%A7%8B-%E4%BB%A5%E6%BE%B3%E6%B4%B2%E4%BA%9E%E9%A6%AC%E9%81%9C%E7%82%BA%E4%BE%8B-584e9c564079)
  * [澳洲微軟雲端架構師 Microsoft Azure Cloud Solution Architect 面試心得 (同場加映 AWS 面試心得)](https://medium.com/@cloudarchitectec/%E6%BE%B3%E6%B4%B2%E5%BE%AE%E8%BB%9F%E9%9B%B2%E7%AB%AF%E6%9E%B6%E6%A7%8B%E5%B8%AB-microsoft-azure-cloud-solution-architect-%E9%9D%A2%E8%A9%A6%E5%BF%83%E5%BE%97-%E5%90%8C%E5%A0%B4%E5%8A%A0%E6%98%A0-aws-%E9%9D%A2%E8%A9%A6%E5%BF%83%E5%BE%97-9dff9fc59ae8)



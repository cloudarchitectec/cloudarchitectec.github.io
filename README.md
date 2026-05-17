# 澳洲雲端架構師 EC 的部落格 | Cloud Architect EC's Blog

[![Blog Deployment](https://github.com/cloudarchitectec/cloudarchitectec.github.io/actions/workflows/blog-deployment.yml/badge.svg)](https://github.com/cloudarchitectec/cloudarchitectec.github.io/actions/workflows/blog-deployment.yml) [![Analytics Update](https://github.com/cloudarchitectec/cloudarchitectec.github.io/actions/workflows/update-analytics.yml/badge.svg?branch=main)](https://github.com/cloudarchitectec/cloudarchitectec.github.io/actions/workflows/update-analytics.yml)

🌐 **Live Blog**: [https://cloudarchitectec.github.io](https://cloudarchitectec.github.io)

## About

This repository hosts the source code for Cloud Architect EC's blog, built with [Hugo](https://gohugo.io/) and the [PaperMod](https://github.com/adityatelange/hugo-PaperMod) theme.

### Topics Covered
- ☁️ Cloud Architecture (AWS, Azure)
- 🛠️ DevOps & Infrastructure
- 📚 Tech Career & Professional Development
- 🇦🇺 Tech Life in Australia
- 📝 Technical Tutorials & Guides

## Tech Stack

- **Static Site Generator**: [Hugo](https://gohugo.io/) (v0.135.0+)
- **Theme**: [PaperMod](https://github.com/adityatelange/hugo-PaperMod)
- **Deployment**: GitHub Actions → GitHub Pages


## Features

- 🌙 Dark/Light mode toggle
- 📱 Fully responsive design
- 🔍 Built-in search functionality
- 📊 Reading time estimation
- 🔗 Social sharing buttons
- 🧭 Breadcrumb navigation
- 🏷️ Tag and category system


## Changelog

All notable changes to this project will be documented in this file.

---

### [2026.05.17]

#### Changed
- Improved search functionality — fixed duplicate results caused by language settings
- Improved converter script to resolve Unsplash image download issue

#### Removed
- Popular posts

---

### [2025.10.19]

#### Added
- Share buttons for Facebook, Threads, Email, and Copy Link

#### Changed
- Improved Google Analytics implementation

#### Fixed
- Commented out broken image generation code in `python/script/automated_blog_converter.py`

---

### [2025.10.12]

#### Added
- `automated_blog_converter.py` to convert formatted Hugo blog posts
- Google stats on landing page
- Popular posts page

#### Fixed
- Categories, tags, and related format/shortcode issues

#### Removed
- Unused TailwindCSS dependency

---

### [2025.10.05]

#### Added
- Imported all coding bootcamp blogs from Blogger
- Bootcamp category
- Automated post list page generation by categories

#### Fixed
- Minor fixes

---

### [2025.10.04]

#### Added
- Email subscription via Google Forms
- First post

#### Changed
- Updated footer

---

### [2025.09.30]

#### Added
- Schema.org configuration
- Alt text to images

#### Changed
- Configured Google Search Console

#### Fixed
- Tags, pagination, images, and titles

---

### [2025.09.29]

#### Added
- 3 missing posts
- Centralised footer; updated footers across all posts

#### Changed
- Configured Google Analytics and logo

#### Fixed
- All internal reference links and categories

---

### [2025.09.28]

#### Added
- Tags and categories
- Search functionality

#### Changed
- Updated home page to feature images and post titles

#### Fixed
- Theme and deployment
- Started reference link cleanup

---

### [2025.09.15]

#### Added
- Initial setup

## License

Content is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
Code is licensed under [MIT License](https://opensource.org/licenses/MIT).

---

*Built with ❤️ using Hugo and PaperMod*
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

**2026.06.20**
- Added custom domain
- Added buy EC a coffee
- Implemented Remark42 comments
- Update action references

**2026.05.17**
- Improved search functionality — fixed duplicate results caused by language settings
- Improved converter script to resolve Unsplash image download issue
- Removed popular posts

**2025.10.19**
- Improved Google Analytics implementation
- Commented out broken image generation code in `tools/blog-converter/automated_blog_converter.py`
- Added share buttons for Facebook, Threads, Email, and Copy Link

**2025.10.12**
- Fixed categories, tags, and related format/shortcode issues
- Added `automated_blog_converter.py` to convert formatted Hugo blog posts
- Removed unused TailwindCSS dependency
- Added Google stats on landing page
- Added popular posts page

**2025.10.05**
- Imported all coding bootcamp blogs from Blogger
- Added bootcamp category
- Automated post list page generation by categories
- Minor fixes

**2025.10.04**
- Updated footer
- Added email subscription via Google Forms
- First post

**2025.09.30**
- Fixed tags, pagination, images, and titles
- Configured Google Search Console
- Added Schema.org configuration
- Added alt text to images

**2025.09.29**
- Fixed all internal reference links and categories
- Added 3 missing posts
- Centralised footer; updated footers across all posts
- Configured Google Analytics and logo

**2025.09.28**
- Fixed theme and deployment
- Added tags and categories
- Updated home page to feature images and post titles
- Added search functionality
- Started reference link cleanup

**2025.09.15**
- Initial setup

--
## License

Content is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
Code is licensed under [MIT License](https://opensource.org/licenses/MIT).
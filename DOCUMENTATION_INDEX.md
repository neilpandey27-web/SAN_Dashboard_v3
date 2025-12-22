# 📚 Documentation Index

**OneIT SAN Analytics v2.0.0**  
**Last Updated:** December 11, 2025

---

## 🎯 Quick Navigation

This project has been reorganized with **consolidated, comprehensive documentation**. All documentation is now organized into **4 main files** plus this index and the README.

---

## 📖 Main Documentation Files

### 1. **README.md** - Project Overview
**Start here for a quick introduction to the project.**

**Contents:**
- Project description and goals
- Quick start guide
- Main features summary
- Recent updates (December 2025 fixes)
- Basic usage instructions
- Support and troubleshooting links

**When to use:** First-time users, overview of the project

---

### 2. **DEPLOYMENT_GUIDE.md** - Setup & Deployment
**Complete guide for setting up and deploying the application.**

**Contents:**
- Quick start (Docker)
- Docker setup (Compose, networking, commands)
- Local development setup (Backend, Frontend)
- Mac-specific setup instructions
- Database configuration (PostgreSQL, SQLite)
- Production deployment checklist
- Docker rebuild instructions
- Complete troubleshooting guide

**When to use:** Setting up the project, deployment, Docker issues, configuration problems

**Size:** ~14KB | **Sections:** 7 major sections

---

### 3. **FIXES_AND_UPDATES.md** - Changes & Fixes
**Documentation of all fixes, updates, and changes.**

**Contents:**
- Recent fixes (December 2025)
  - Database Management Tooltips
  - Storage Systems Columns
  - CSV Download Feature
- Storage Systems Drill-Down fix details
- Data preprocessing changes
- Verification guides for each fix
- Download links for fixes
- Deployment instructions after fixes

**When to use:** Understanding recent changes, verifying fixes work, debugging new issues

**Size:** ~13KB | **Sections:** 5 major sections

---

### 4. **DATABASE_DOCUMENTATION.md** - Database Details
**Everything about database persistence, schemas, and operations.**

**Contents:**
- Database overview (PostgreSQL, SQLite)
- Data persistence explained (What gets saved where?)
- Docker and database persistence (Volume mounting)
- Database initialization (Seed data)
- Database schema (All tables)
- Calculated fields and unique constraints
- Data export and backup procedures
- Database troubleshooting

**When to use:** Database questions, data persistence, backup/restore, schema information

**Size:** ~18KB | **Sections:** 7 major sections

---

### 5. **TECHNICAL_SPECIFICATIONS.md** - Features & Technical Details
**Comprehensive technical documentation for developers.**

**Contents:**
- Complete features overview
- Technology stack (Frontend, Backend, DevOps)
- Application architecture (Diagrams, request flow)
- API endpoints (Full reference)
- Data models (Database schemas)
- Metrics and calculations
- Excel upload format specifications
- Future enhancements roadmap

**When to use:** Development, API integration, understanding architecture, contributing to the project

**Size:** ~17KB | **Sections:** 8 major sections

---

## 🗂️ Old Documentation Archive

Old documentation files have been moved to `/old_docs_backup/` directory for reference.

**Why consolidated?**
- Previously: **30+ scattered documentation files**
- Now: **4 comprehensive, well-organized files**
- Benefits: Easier to find information, reduced duplication, better maintenance

---

## 🔍 How to Find What You Need

### **I want to...**

#### **...set up the project for the first time**
→ Read `README.md` first, then `DEPLOYMENT_GUIDE.md`

#### **...understand recent fixes**
→ `FIXES_AND_UPDATES.md` → Recent Fixes section

#### **...deploy to Docker**
→ `DEPLOYMENT_GUIDE.md` → Docker Setup section

#### **...understand database persistence**
→ `DATABASE_DOCUMENTATION.md` → Data Persistence Explained

#### **...troubleshoot an issue**
→ `DEPLOYMENT_GUIDE.md` → Troubleshooting section

#### **...back up the database**
→ `DATABASE_DOCUMENTATION.md` → Data Export and Backup

#### **...understand the API**
→ `TECHNICAL_SPECIFICATIONS.md` → API Endpoints section

#### **...know what features exist**
→ `TECHNICAL_SPECIFICATIONS.md` → Features Overview

#### **...see the architecture**
→ `TECHNICAL_SPECIFICATIONS.md` → Application Architecture

#### **...verify the three recent fixes work**
→ `FIXES_AND_UPDATES.md` → Verification Guides

#### **...understand Excel upload format**
→ `TECHNICAL_SPECIFICATIONS.md` → Excel Upload Format

#### **...set up local development (not Docker)**
→ `DEPLOYMENT_GUIDE.md` → Local Development Setup

---

## 📊 Documentation Statistics

**Before Consolidation:**
- Total .md files: 30+
- In root directory: 14 files
- In docs/ directory: 13 files
- In old_docs_backup/: 90+ files

**After Consolidation:**
- Main documentation files: **4**
- README.md: **1**
- Documentation index: **1** (this file)
- Total essential files: **6**
- Reduction: **80% fewer files**

---

## 🎯 Documentation Principles

1. **Single Source of Truth**: Each topic covered in exactly one place
2. **Cross-Referenced**: Related topics link to each other
3. **Comprehensive**: All necessary information included
4. **Searchable**: Use browser Ctrl+F to find topics quickly
5. **Up-to-Date**: Reflects current v2.0.0 state with December 2025 fixes

---

## 🔗 Quick Links

### **Project Files**
- Main Documentation: `/home/user/webapp/`
- Backend Code: `/home/user/webapp/backend/`
- Frontend Code: `/home/user/webapp/frontend/`
- Database Files: `/home/user/webapp/db_files/`
- Old Docs Archive: `/home/user/webapp/old_docs_backup/`

### **Online Resources**
- Download Complete Application: `https://8000-i65shl7xcwopxsxvhr7d8-b32ec7bb.sandbox.novita.ai/download/webapp-complete-folder`
- Download Fixes Only: `https://8000-i65shl7xcwopxsxvhr7d8-b32ec7bb.sandbox.novita.ai/download/webapp-three-fixes-complete`
- API Documentation: `http://localhost:8000/api/docs` (when running)

---

## 📝 Documentation Maintenance

### **When to Update Documentation**

- ✅ New features added
- ✅ Fixes applied
- ✅ Configuration changes
- ✅ API endpoint changes
- ✅ Deployment process changes

### **Which File to Update**

| Change Type | Update File |
|------------|-------------|
| New feature | `TECHNICAL_SPECIFICATIONS.md` |
| Setup/deployment change | `DEPLOYMENT_GUIDE.md` |
| Bug fix | `FIXES_AND_UPDATES.md` |
| Database schema change | `DATABASE_DOCUMENTATION.md` |
| Overview/quick start | `README.md` |

---

## 🆘 Still Can't Find What You Need?

1. **Use browser search** (Ctrl+F / Cmd+F) in the relevant documentation file
2. **Check old documentation** in `/old_docs_backup/` if needed
3. **Review API docs** at `http://localhost:8000/api/docs`
4. **Check browser console** (F12) for frontend errors
5. **Check Docker logs**: `docker compose logs frontend` or `backend`

---

## ✅ Documentation Status

- ✅ **DEPLOYMENT_GUIDE.md** - Complete, up-to-date
- ✅ **FIXES_AND_UPDATES.md** - Complete, includes December 2025 fixes
- ✅ **DATABASE_DOCUMENTATION.md** - Complete, comprehensive
- ✅ **TECHNICAL_SPECIFICATIONS.md** - Complete, includes all features
- ✅ **README.md** - Updated with latest information
- ✅ **DOCUMENTATION_INDEX.md** - This file, navigation guide

---

**Total Documentation Size:** ~60KB (compressed, readable)  
**Previous Documentation Size:** ~150KB+ (scattered, redundant)  
**Improvement:** 60% size reduction, 80% fewer files, 100% better organization

---

**Last Updated:** December 11, 2025  
**Version:** 2.0.0  
**Status:** ✅ Complete documentation consolidation

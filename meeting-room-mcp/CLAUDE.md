# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Environment Setup
- `uv sync` - Install dependencies using uv
- `uv run python -m venv .venv` - Create virtual environment
- `source .venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows) - Activate virtual environment

### Running the Application
- `uv run python scripts/start_server.py` - Start the MCP server
- `uv run python -m src.meeting_room_mcp.server.main` - Alternative way to run server

### Code Quality Tools
- `uv run black .` - Format code with Black
- `uv run ruff check .` - Run linting with Ruff
- `uv run ruff check . --fix` - Auto-fix linting issues
- `uv run mypy src/` - Run type checking
- `uv run pytest` - Run tests

### Database Operations
The application uses MySQL with SQLAlchemy. Database settings are configured in `.env` file.

## Architecture Overview

This is a **Meeting Room Reservation MCP (Model Context Protocol) Server** built with FastAPI and FastMCP. The system provides conversational meeting room booking capabilities through LLM integrations.

### Core Components

**MCP Server Layer** (`src/meeting_room_mcp/server/`)
- `main.py` - FastMCP application with tool definitions for room search, reservation management, and session handling
- `tools/` - Individual tool implementations (search, reservation, session management)
- `handlers/` - Session management for conversational booking flows

**Shared Business Logic** (`src/meeting_room_mcp/shared/`)
- `database.py` - SQLAlchemy-based MySQL database manager with entities and models
- `models.py` - Pydantic dataclasses for MeetingRoom, Reservation, ReservationSession, and related types
- `email_service.py` - Email notification service with SMTP and mock modes

**Configuration** (`src/meeting_room_mcp/config/`)
- `settings.py` - Pydantic Settings with multiple configuration classes (DatabaseSettings, EmailSettings, LLMSettings)

### Key Architectural Patterns

**Conversational Booking Flow**
- Uses `ReservationSession` model to track multi-turn conversations
- Session manager handles incomplete information gathering
- Natural language processing for reservation requests

**Tool-based MCP Interface**
- Each major function exposed as MCP tools (search_available_rooms, create_reservation, etc.)
- Tools handle both direct reservations and conversational flows
- Database operations abstracted through DatabaseManager

**Multi-Environment Configuration**
- Environment-specific settings (development, test, production)
- Settings validation with required field checking
- Separate configuration classes for different concerns

### Database Schema
- **meeting_rooms** - Room information with capacity, location, equipment
- **reservations** - Booking details with time slots and participant lists
- Uses MySQL with connection pooling and proper indexing

### Email System
- Supports both real SMTP and mock mode for development
- Automatic notifications for reservations and cancellations
- Template-based email generation

## Development Notes

**Environment Configuration**
- Copy `.env.example` to `.env` and configure database and email settings
- MySQL database must be set up separately
- Email mock mode is enabled by default for development

**Session Management**
- Reservation sessions are stored in JSON files (`data/sessions.json`)
- Automatic cleanup of old sessions (24-hour default)
- Session state tracks conversation progress and collected information

**Error Handling**
- Comprehensive logging throughout the application
- Graceful degradation for email service failures
- Validation at both Pydantic model and database levels
from bot_corrected import app

if __name__ == "__main__":
    print("✅ Bot is running on Railway!")
    app.run_polling(drop_pending_updates=True)

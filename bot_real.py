import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from scraper_real import get_facebook_info_real

# ========== CẤU HÌNH ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    logger.error("❌ LỖI: Chưa thiết lập BOT_TOKEN!")
    exit(1)

# ========== XỬ LÝ LỆNH ==========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /start"""
    help_text = """
🤖 *Bot Check Facebook Info - REAL VERSION*

*Cách sử dụng:*
• Gửi *username* Facebook (ví dụ: `zuck`)
• Hoặc *UID* (ví dụ: `1000`)

*Lưu ý quan trọng:*
⚠️ Chỉ hoạt động với trang *công khai* (public)
⚠️ Tốc độ phụ thuộc vào Facebook
⚠️ Có thể không lấy được tất cả thông tin

*Ví dụ:* `facebook` `cristiano` `taylor.swift`
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý tin nhắn người dùng"""
    user_input = update.message.text.strip()
    user_id = update.message.from_user.id
    
    logger.info(f"User {user_id} yêu cầu: {user_input}")
    
    # Thông báo đang xử lý
    processing_msg = await update.message.reply_text(
        f"🔍 *Đang thu thập thông tin cho:* `{user_input}`\n⏳ Vui lòng đợi 10-20 giây...",
        parse_mode='Markdown'
    )
    
    try:
        # Gọi hàm thu thập THẬT
        result = get_facebook_info_real(user_input)
        
        # Kiểm tra kết quả
        if not result.get('success', False):
            error_msg = result.get('error', 'Lỗi không xác định')
            await update.message.reply_text(
                f"❌ *Không thể lấy thông tin!*\n\n"
                f"• **Username/UID:** `{user_input}`\n"
                f"• **Lý do:** {error_msg}\n\n"
                f"_Gợi ý:_\n1. Kiểm tra username có đúng không\n"
                f"2. Trang có thể không công khai\n"
                f"3. Thử lại sau vài phút",
                parse_mode='Markdown'
            )
            await processing_msg.delete()
            return
        
        # ========== ĐỊNH DẠNG KẾT QUẢ THẬT ==========
        result_text = f"""
📋 *THÔNG TIN FACEBOOK - THẬT*
━━━━━━━━━━━━━━━━━━━━
👤 **Tên:** {result.get('name', 'Không xác định')}
🆔 **UID:** `{result.get('uid', 'N/A')}`
📛 **Username:** `{result.get('username', 'N/A')}`
✅ **Verified:** {result.get('verified', 'Không')}

📊 **Thống kê:**
• 👥 {result.get('followers', 'Không công khai')}

📍 **Thông tin khác:**
• 📝 {result.get('bio', 'Không có mô tả')}
• 🔗 {result.get('url', 'N/A')}
• 🕒 Thu thập lúc: {result.get('scraped_at', 'N/A')}

━━━━━━━━━━━━━━━━━━━━
⚠️ *Thông tin chỉ từ dữ liệu CÔNG KHAI*
📌 Facebook có thể chặn truy cập tự động
        """
        
        # Gửi ảnh đại diện nếu có
        avatar_url = result.get('avatar_url')
        if avatar_url and avatar_url.startswith('http'):
            try:
                await update.message.reply_photo(
                    photo=avatar_url,
                    caption=result_text,
                    parse_mode='Markdown'
                )
            except:
                await update.message.reply_text(result_text, parse_mode='Markdown')
        else:
            await update.message.reply_text(result_text, parse_mode='Markdown')
        
        await processing_msg.delete()
        
    except Exception as e:
        logger.error(f"Lỗi xử lý: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ *Lỗi hệ thống!*\n\nBot gặp sự cố khi xử lý yêu cầu. Vui lòng thử lại sau.",
            parse_mode='Markdown'
        )
        await processing_msg.delete()

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lỗi toàn cục"""
    logger.error(f"Lỗi: {context.error}", exc_info=True)
    if update and update.message:
        await update.message.reply_text("❌ Đã xảy ra lỗi hệ thống!")

# ========== HÀM CHÍNH ==========
def main():
    """Khởi chạy bot"""
    try:
        # Tạo application
        app = Application.builder().token(TOKEN).build()
        
        # Đăng ký handlers
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", start_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Error handler
        app.add_error_handler(error_handler)
        
        # Khởi động
        logger.info("🤖 Bot REAL đang khởi động...")
        app.run_polling()
        
    except Exception as e:
        logger.error(f"Lỗi khởi động: {e}")

if __name__ == '__main__':
    main()
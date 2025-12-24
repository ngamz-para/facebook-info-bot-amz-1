import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from scraper_improved import get_facebook_info_improved  # Đảm bảo import đúng

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
🤖 *Bot Check Facebook Info - VERSION 2.0*

*Cách sử dụng:*
• Gửi *username* Facebook (ví dụ: `facebook`)

*Cải tiến mới:*
⚡ Tốc độ nhanh hơn (5-10s)
✅ Phát hiện verified chính xác hơn
📅 Ước lượng năm tham gia dựa trên UID

⚠️ *Lưu ý:* Chỉ hoạt động với trang *công khai*
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý tin nhắn người dùng"""
    user_input = update.message.text.strip()
    user_id = update.message.from_user.id
    
    logger.info(f"User {user_id} yêu cầu: {user_input}")
    
    processing_msg = await update.message.reply_text(
        f"🔍 *Đang thu thập:* `{user_input}`\n⏳ Vui lòng đợi 5-10 giây...",
        parse_mode='Markdown'
    )
    
    try:
        result = get_facebook_info_improved(user_input)
        
        if not result.get('success', False):
            error_msg = result.get('error', 'Lỗi không xác định')
            await update.message.reply_text(
                f"❌ *Không thể lấy thông tin!*\n• **Lý do:** {error_msg}",
                parse_mode='Markdown'
            )
            await processing_msg.delete()
            return
        
        # ĐỊNH DẠNG KẾT QUẢ
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
• 📅 **Tham gia:** {result.get('estimated_join_date', 'Không rõ')}
• 🔗 {result.get('url', 'N/A')}
• ⚡ Thu thập trong: {result.get('scraped_in', 'N/A')}
• 🕒 Lúc: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━
⚠️ *Thông tin từ dữ liệu CÔNG KHAI*
📌 Ngày tham gia là ƯỚC LƯỢNG
"""
        
        # Gửi ảnh nếu có
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
        logger.error(f"Lỗi: {e}", exc_info=True)
        await update.message.reply_text("❌ Lỗi hệ thống! Thử lại sau.")
        await processing_msg.delete()

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Lỗi toàn cục: {context.error}")

# ========== HÀM CHÍNH ==========
def main():
    try:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", start_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_error_handler(error_handler)
        
        logger.info("🤖 Bot đang khởi động...")
        app.run_polling()
        
    except Exception as e:
        logger.error(f"Lỗi khởi động: {e}")

if __name__ == '__main__':
    main()

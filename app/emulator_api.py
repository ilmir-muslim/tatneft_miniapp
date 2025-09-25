from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db

router = APIRouter()


@router.get("/payment-emulator/{payment_id}", response_class=HTMLResponse)
async def payment_emulator_page(
    request: Request, payment_id: str, db: Session = Depends(get_db)
):
    """Страница эмуляции банковского платежа"""

    from app.utils.alfa_payment_emulator import alfa_emulator

    try:
        payment_info = await alfa_emulator.get_payment_status(payment_id)
        order_data = payment_info.get("order_data", {})

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Эмулятор Альфа-Банка</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    max-width: 500px; 
                    margin: 0 auto; 
                    padding: 20px;
                    background: linear-gradient(135deg, #ef3124 0%, #cc1f14 100%);
                    min-height: 100vh;
                    color: white;
                }}
                .container {{ 
                    background: white; 
                    color: #333;
                    border-radius: 15px; 
                    padding: 25px; 
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    margin-top: 20px;
                }}
                .header {{ 
                    background: #ef3124; 
                    color: white; 
                    padding: 20px; 
                    margin: -25px -25px 25px -25px; 
                    border-radius: 15px 15px 0 0; 
                    text-align: center;
                }}
                .amount {{ 
                    font-size: 32px; 
                    font-weight: bold; 
                    text-align: center; 
                    margin: 25px 0; 
                    color: #2c3e50;
                }}
                .order-details {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 10px;
                    margin: 15px 0;
                    font-size: 14px;
                }}
                .button {{ 
                    display: block; 
                    width: 100%; 
                    padding: 15px; 
                    margin: 10px 0; 
                    border: none; 
                    border-radius: 8px; 
                    font-size: 16px; 
                    cursor: pointer; 
                    transition: all 0.3s;
                    text-align: center;
                    text-decoration: none;
                }}
                .success {{ 
                    background: #27ae60; 
                    color: white; 
                }}
                .success:hover {{ background: #219653; }}
                .warning {{ 
                    background: #f39c12; 
                    color: white; 
                }}
                .warning:hover {{ background: #e67e22; }}
                .cancel {{ 
                    background: #e74c3c; 
                    color: white; 
                }}
                .cancel:hover {{ background: #c0392b; }}
                .info {{ 
                    background: #3498db; 
                    color: white; 
                }}
                .info:hover {{ background: #2980b9; }}
                .logo {{ 
                    text-align: center; 
                    margin-bottom: 20px; 
                    font-size: 24px;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="logo">Альфа-Банк</div>
            <div class="container">
                <div class="header">
                    <h2>Оплата заказа</h2>
                    <p>Эмулятор платежной системы</p>
                </div>
                
                <div class="amount">{payment_info['amount']:.2f} ₽</div>
                
                <div class="order-details">
                    <p><strong>Детали заказа:</strong></p>
                    <p>АЗС: №{order_data.get('azs_number', 'N/A')}</p>
                    <p>Колонка: {order_data.get('column_number', 'N/A')}</p>
                    <p>Топливо: {order_data.get('fuel_type', 'N/A')}</p>
                    <p>ID заказа: {payment_info['order_id']}</p>
                </div>
                
                <p>Выберите результат для тестирования:</p>
                
                <form action="/payment-emulator/{payment_id}/process" method="post">
                    <button type="submit" name="action" value="success" class="button success">
                        ✅ Успешный платеж
                    </button>
                    
                    <button type="submit" name="action" value="fail" class="button warning">
                        ⚠️ Отказ банка
                    </button>
                    
                    <button type="submit" name="action" value="cancel" class="button cancel">
                        ❌ Отменить платеж
                    </button>
                </form>
                
                <a href="#" onclick="window.close()" class="button info">
                    🔄 Вернуться в приложение
                </a>
            </div>
            
            <script>
                // Автоматическое закрытие после успешной оплаты (для тестирования)
                function autoCloseAfterPayment() {{
                    const urlParams = new URLSearchParams(window.location.search);
                    if (urlParams.get('autoClose') === 'true') {{
                        setTimeout(() => window.close(), 2000);
                    }}
                }}
                autoCloseAfterPayment();
            </script>
        </body>
        </html>
        """

        return HTMLResponse(content=html_content)

    except Exception as e:
        return HTMLResponse(content=f"<h1>Ошибка: {str(e)}</h1>")


@router.post("/payment-emulator/{payment_id}/process")
async def process_emulated_payment(
    payment_id: str, action: str = Form(...), db: Session = Depends(get_db)
):
    """Обработка эмулированного платежа"""

    from app.utils.alfa_payment_emulator import alfa_emulator
    from app.utils.notifications import notify_order_update

    try:
        # Обрабатываем платеж
        result = await alfa_emulator.process_payment(payment_id, action)

        # Отправляем вебхук (как это сделал бы реальный банк)
        webhook_data = {
            "orderId": payment_id,
            "status": result["status"],
            "reason": result.get("message", ""),
            "transactionId": result.get("transaction_id"),
        }

        await alfa_emulator.handle_webhook(db, webhook_data)

        # Уведомляем через WebSocket
        payment_info = await alfa_emulator.get_payment_status(payment_id)
        await notify_order_update(
            payment_info["order_id"],
            "принято" if result["status"] == "COMPLETED" else "отказано",
            result.get("message"),
        )

        # Перенаправляем на страницу результата
        return RedirectResponse(
            url=f"/payment-emulator/{payment_id}/result?status={result['status']}&message={result.get('message', '')}",
            status_code=303,
        )

    except Exception as e:
        return HTMLResponse(content=f"<h1>Ошибка: {str(e)}</h1>")


@router.get("/payment-emulator/{payment_id}/result", response_class=HTMLResponse)
async def payment_result_page(payment_id: str, status: str, message: str = ""):
    """Страница результата платежа"""

    from app.utils.alfa_payment_emulator import alfa_emulator

    try:
        payment_info = await alfa_emulator.get_payment_status(payment_id)

        is_success = status == "COMPLETED"
        title = "Платеж успешно завершен" if is_success else "Платеж не прошел"
        icon = "✅" if is_success else "❌"
        color = "#27ae60" if is_success else "#e74c3c"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Результат платежа</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    padding: 50px 20px;
                    background: linear-gradient(135deg, {color} 0%, #2c3e50 100%);
                    color: white;
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                }}
                .result-container {{
                    background: white;
                    color: #333;
                    padding: 30px;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    max-width: 400px;
                }}
                .icon {{ 
                    font-size: 80px; 
                    margin-bottom: 20px;
                }}
                .message {{ 
                    font-size: 18px; 
                    margin: 20px 0;
                    line-height: 1.5;
                }}
                .details {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 10px;
                    margin: 15px 0;
                    font-size: 14px;
                    text-align: left;
                }}
                .close-btn {{
                    display: inline-block;
                    background: #3498db;
                    color: white;
                    padding: 12px 24px;
                    border: none;
                    border-radius: 8px;
                    font-size: 16px;
                    cursor: pointer;
                    margin-top: 20px;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            <div class="result-container">
                <div class="icon">{icon}</div>
                <h1>{title}</h1>
                <div class="message">{message}</div>
                
                <div class="details">
                    <p><strong>ID платежа:</strong> {payment_id}</p>
                    <p><strong>Сумма:</strong> {payment_info['amount']:.2f} ₽</p>
                    <p><strong>Статус:</strong> {status}</p>
                    {f'<p><strong>Номер транзакции:</strong> {payment_info.get("transaction_id", "N/A")}</p>' if is_success else ''}
                </div>
                
                <p><small>Это окно можно закрыть</small></p>
                <button onclick="window.close()" class="close-btn">Закрыть окно</button>
            </div>
            
            <script>
                // Автоматическое закрытие через 3 секунды
                setTimeout(() => {{
                    window.close();
                }}, 3000);
                
                // Отправляем сообщение родительскому окну (если оно есть)
                if (window.opener) {{
                    window.opener.postMessage({{
                        type: 'payment_completed',
                        payment_id: '{payment_id}',
                        status: '{status}',
                        message: '{message}'
                    }}, '*');
                }}
            </script>
        </body>
        </html>
        """

        return HTMLResponse(content=html_content)

    except Exception as e:
        return HTMLResponse(content=f"<h1>Ошибка: {str(e)}</h1>")


@router.get("/payment-emulator/status/{order_id}")
async def get_payment_status_by_order(order_id: int, db: Session = Depends(get_db)):
    """Получение статуса платежа по ID заказа"""
    from app.utils.alfa_payment_emulator import alfa_emulator

    try:
        payment = alfa_emulator.get_payment_by_order_id(order_id)
        if payment:
            return {
                "status": "found",
                "payment_status": payment.get("status"),
                "transaction_id": payment.get("transaction_id"),
                "failure_reason": payment.get("failure_reason"),
            }
        else:
            return {"status": "not_found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

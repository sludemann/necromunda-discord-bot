from datetime import datetime,timezone
from db import get_connection

def log_transaction(gang_id: int, change: int, reason: str, user_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO gang_transactions (gang_id, change, reason, user_id) VALUES (?, ?, ?, ?)", (gang_id, change, reason, user_id))
    conn.commit()
    conn.close()

def get_current_credits(gang_id: int) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT SUM(change) FROM gang_transactions WHERE gang_id = ?", (gang_id,))
    total = c.fetchone()[0]
    conn.close()
    return total if total is not None else 0

def get_transaction_history(
    gang_id: int,
    overall_current_credits: int,
    limit: int = 10,
    offset: int = 0
) -> tuple[list[tuple[any, int, str, int]], int]:
    """
    Fetches a paginated list of transactions for a gang, including a calculated
    running total (balance after each transaction) for display.

    Args:
        gang_id: The ID of the gang.
        overall_current_credits: The gang's absolute current total credits.
        limit: Number of transactions per page.
        offset: Offset for pagination ( (page - 1) * limit ).

    Returns:
        A tuple containing:
        - page_transactions_with_rt: List of tuples:
          (timestamp_dt, change, reason, running_total_after_this_transaction).
          Transactions are ordered newest first.
        - total_transactions_count: Total number of transactions for the gang.
    """
    conn = get_connection() # Your actual database connection function
    c = conn.cursor()

    sum_of_changes_on_newer_pages = 0
    if offset > 0:
        c.execute(
            """
            SELECT COALESCE(SUM(change), 0)
            FROM (
                SELECT change
                FROM gang_transactions
                WHERE gang_id = ?
                ORDER BY timestamp DESC
                LIMIT ?  -- This limit is the 'offset' value
            ) AS newer_transactions;
            """,
            (gang_id, offset)
        )
        sum_row = c.fetchone()
        if sum_row:
            sum_of_changes_on_newer_pages = sum_row[0]

    page_start_ref_balance = overall_current_credits - sum_of_changes_on_newer_pages
    query = """
    WITH PagedTransactions AS (
        SELECT
            timestamp,
            change,
            reason,
            -- Sum of 'change' for rows from the start of this page's result set (newest)
            -- up to 1 row PRECEDING the current row within this page's result set.
            COALESCE(
                SUM(change) OVER (ORDER BY timestamp DESC ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),
                0
            ) AS sum_of_prior_changes_on_page
        FROM gang_transactions
        WHERE gang_id = :gang_id
        ORDER BY timestamp DESC
        LIMIT :limit OFFSET :offset
    )
    SELECT
        timestamp,
        change,
        reason,
        -- Calculate the balance AFTER the current transaction
        (:page_start_ref_balance - sum_of_prior_changes_on_page) AS running_total_after_transaction
    FROM PagedTransactions;
    """
    c.execute(query, {
        "gang_id": gang_id,
        "limit": limit,
        "offset": offset,
        "page_start_ref_balance": page_start_ref_balance
    })
    raw_page_data_with_rt = c.fetchall()

    history: list[tuple[any, int, str, int]] = []
    for ts_str, change_val, reason_str, rt_after_tx in raw_page_data_with_rt:
        try:
            # Assuming timestamp_str is 'YYYY-MM-DD HH:MM:SS' and stored in UTC
            dt_naive = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            timestamp_dt = dt_naive.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError) as e:
            # Robust error handling for timestamp parsing
            print(f"Warning: Could not parse timestamp '{ts_str}' for gang {gang_id}: {e}")
            timestamp_dt = datetime.min.replace(tzinfo=timezone.utc) # Fallback
        history.append(
            (timestamp_dt, change_val, reason_str, rt_after_tx)
        )

    # Step 4: Get the total count of transactions for this gang for pagination
    c.execute(
        "SELECT COUNT(*) FROM gang_transactions WHERE gang_id = ?",
        (gang_id,)
    )
    count_row = c.fetchone()
    total_transactions_count = count_row[0] if count_row else 0

    conn.close()

    return history, total_transactions_count
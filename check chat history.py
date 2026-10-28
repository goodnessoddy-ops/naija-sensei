"""
Shows what chat history is really in the database, and whether the automatic clearing rule
is set. Run it in the same folder as server.py:

    python check_chat_history.py

It only READS. It changes nothing.
"""
from dotenv import load_dotenv
load_dotenv()
from auth import _get_conn, get_waec_end_date

conn = _get_conn()
print("\n=== Automatic clearing rule ===")
print("WAEC end date set in the admin panel:", get_waec_end_date() or "(none set)")
print("(Chats are wiped 3 months after that date, once; with no date they clear after long inactivity.)")

print("\n=== Chat history in the database ===")
total = conn.execute("SELECT COUNT(*) AS c FROM chat_history").fetchone()["c"]
print("Total messages stored:", total)

rows = conn.execute("""
    SELECT u.username, COUNT(*) AS n,
           SUM(CASE WHEN h.subject IS NULL THEN 1 ELSE 0 END) AS general_msgs,
           SUM(CASE WHEN h.subject IS NOT NULL AND h.topic IS NULL THEN 1 ELSE 0 END) AS subject_msgs,
           SUM(CASE WHEN h.topic IS NOT NULL THEN 1 ELSE 0 END) AS topic_msgs,
           MIN(h.created_at) AS oldest, MAX(h.created_at) AS newest
    FROM chat_history h JOIN users u ON u.id = h.user_id
    GROUP BY u.username ORDER BY n DESC
""").fetchall()
print(f"\n{'user':<18}{'total':>6}{'general':>9}{'subject':>9}{'topic':>7}   oldest -> newest")
for r in rows:
    print(f"{str(r['username']):<18}{r['n']:>6}{r['general_msgs']:>9}{r['subject_msgs']:>9}{r['topic_msgs']:>7}   {r['oldest']} -> {r['newest']}")
if not rows:
    print("(no chat messages at all)")

print("\n=== Last activity per student ===")
for r in conn.execute("SELECT u.username, a.last_active FROM user_activity a JOIN users u ON u.id = a.user_id ORDER BY a.last_active DESC").fetchall():
    print(f"{str(r['username']):<18}{r['last_active']}")
conn.close()
print("""
How to read this:
- Your old messages are listed with an 'oldest' date from before the problem  -> they were NOT deleted
  (something is hiding them on screen, tell me which chat looks empty).
- 'oldest' is only a few minutes/hours ago for your user                      -> they WERE deleted
  (most likely by the automatic clearing rule above).
""")
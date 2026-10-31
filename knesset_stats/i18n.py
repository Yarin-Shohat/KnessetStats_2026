"""English / Hebrew UI translations.

The English text itself is the lookup key, so English needs no table and a string without a
translation falls back to English (and is recorded in ``MISSING`` for tests).
"""
from __future__ import annotations

from typing import Callable

from .explanations import HE_EXPLANATIONS

LANGUAGES: dict[str, str] = {"en": "English", "he": "עברית"}

# Keys that were requested in Hebrew mode but have no translation (inspected by tests).
MISSING: set[str] = set()

HE: dict[str, str] = {
    # --- Page, sidebar, status ---------------------------------------------------------------
    "Knesset Stats | Polls vs Results": "סטטיסטיקת הכנסת | סקרים מול תוצאות",
    "Settings": "הגדרות",
    "Data sources": "מקורות הנתונים",
    "Created by [Yarin Shohat](https://www.linkedin.com/in/yarinsh/)":
        "נוצר על ידי [Yarin Shohat](https://www.linkedin.com/in/yarinsh/)",
    "Election results per locality: [Kaplan Open Source - Elections](https://elections.kaplanopensource.co.il/"
    "locality/), based on the official results of the Central Elections Committee.":
        "תוצאות הבחירות לפי יישוב: [Kaplan Open Source - Elections](https://elections.kaplanopensource.co.il/"
        "locality/), המבוססות על התוצאות הרשמיות של ועדת הבחירות המרכזית.",
    "Pre-election polls: published by TV channels 11, 12, 13, 14, 16 and 24 and the polling firms that "
    "conducted them. Only the extracted figures are analysed.":
        "סקרי טרום בחירות: פורסמו על ידי ערוצי הטלוויזיה 11, 12, 13, 14, 16 ו-24 ועל ידי חברות הסקרים שביצעו "
        "אותם. מנותחים רק הנתונים שחולצו מהם.",
    "All data belongs to its original publishers and is used for non-commercial statistical analysis.":
        "כל הנתונים שייכים למפרסמיהם המקוריים ומשמשים לניתוח סטטיסטי לא מסחרי.",
    "True-result basis (Tests 4-6)": "בסיס התוצאה האמיתית (מבחנים 4-6)",
    "Official national % (Kaplan site, includes double envelopes)":
        "אחוזים ארציים רשמיים (אתר קפלן, כולל מעטפות כפולות)",
    "Sum of locality vote counts (excludes double envelopes)": "סכום הקולות ביישובים (ללא מעטפות כפולות)",
    "Locality pages omit double-envelope votes (soldiers, diplomats, etc.), which skews shares "
    "slightly towards localities with few such voters. The official national % is the complete figure.":
        "דפי היישובים אינם כוללים קולות במעטפות כפולות (חיילים, דיפלומטים ועוד), ולכן החלקים מוטים מעט "
        "לטובת יישובים עם מעט מצביעים כאלה. האחוז הארצי הרשמי הוא הנתון המלא.",
    "Design effect (poll N is divided by this)": "אפקט התכנון (גודל המדגם N מחולק בו)",
    "1.0 = simple random sample. Online panels, weighting and over-sampling (e.g. Channel 13) "
    "shrink the effective sample, which makes p-values smaller than they should be.":
        "1.0 = מדגם מקרי פשוט. פאנלים מקוונים, שקלול ודגימת יתר (למשל בערוץ 13) מקטינים את המדגם האפקטיבי, "
        "ולכן ערכי p קטנים ממה שראוי.",
    "Significance level α": "רמת מובהקות α",
    "Include Channel 16 (poll dated 2-3 Aug, ~3 months early)":
        "כלול את ערוץ 16 (סקר מ-2-3 באוגוסט, כשלושה חודשים לפני הבחירות)",
    "📊 Knesset 26 vs 25: election shifts and TV-poll accuracy":
        "📊 הכנסת ה-26 מול ה-25: שינויים בבחירות ודיוק סקרי הטלוויזיה",
    "The six PDFs are **pre-election polls** (3 Aug - 23 Oct 2026), not exit polls: the election was on "
    "27 Oct 2026. Poll seat forecasts are compared with the final results after removing undecided, "
    "non-voters and lists that failed the 3.25% threshold.":
        "ששת קובצי ה-PDF הם **סקרי טרום-בחירות** (3 באוגוסט - 23 באוקטובר 2026) ולא סקרי יציאה: הבחירות "
        "התקיימו ב-27 באוקטובר 2026. תחזיות המנדטים בסקרים מושוות לתוצאות הסופיות לאחר הסרת מתלבטים, "
        "לא-מצביעים ורשימות שלא עברו את אחוז החסימה (3.25%).",
    "Reading poll PDFs...": "קורא את קובצי הסקרים...",
    "Fetching locality results (first run takes ~2 minutes, then cached on disk)...":
        "טוען תוצאות לפי יישוב (ההרצה הראשונה אורכת כשתי דקות, לאחר מכן הנתונים נשמרים בדיסק)...",
    "Failed to read the final-results text file: {error}": "קריאת קובץ התוצאות הסופיות נכשלה: {error}",
    "Failed to read {filename}. Please ensure the PDF contains parseable text.":
        "קריאת {filename} נכשלה. ודאו שה-PDF מכיל טקסט הניתן לקריאה.",
    "Failed to load election data from elections.kaplanopensource.co.il: {error}":
        "טעינת נתוני הבחירות מ-elections.kaplanopensource.co.il נכשלה: {error}",
    "{failed} of {total} locality pages failed to load and are excluded.":
        "{failed} מתוך {total} דפי יישובים לא נטענו ולכן הוחרגו.",
    "Could not build the true-result distribution: {error}": "לא ניתן לבנות את התפלגות התוצאה האמיתית: {error}",
    "Cannot run Chi-Square/Z-test for {channel}: Sample size (N) is missing from the PDF.":
        "לא ניתן להריץ מבחן חי בריבוע / Z עבור {channel}: גודל המדגם (N) חסר ב-PDF.",
    "p = {p} ({verdict} at α = {alpha})": "p = {p} ({verdict} ברמת α = {alpha})",
    "significant": "מובהק",
    "not significant": "לא מובהק",
    "pp": "נק' אחוז",
    "ok": "תקין",
    "file not found": "הקובץ לא נמצא",
    "no extractable text": "אין טקסט הניתן לחילוץ",
    # --- Tabs ----------------------------------------------------------------------------------
    "Data quality": "איכות הנתונים",
    "1 · City-level shift": "1 · שינוי ברמת היישוב",
    "2 · Voting map shift": "2 · שינוי במפת ההצבעה",
    "3 · One party nationally": "3 · מפלגה אחת ארצית",
    "4 · Poll accuracy (χ²)": "4 · דיוק הסקרים (χ²)",
    "5 · Single-party miss": "5 · החטאה במפלגה בודדת",
    "6 · War of the channels": "6 · מלחמת הערוצים",
    # --- Channels --------------------------------------------------------------------------------
    "Channel": "ערוץ",
    "Channel 11": "ערוץ 11", "Channel 12": "ערוץ 12", "Channel 13": "ערוץ 13",
    "Channel 14": "ערוץ 14", "Channel 16": "ערוץ 16", "Channel 24": "ערוץ 24",
    # --- Data quality ----------------------------------------------------------------------------
    "Sources and coverage": "מקורות וכיסוי",
    "Localities loaded (26th)": "יישובים שנטענו (הכנסת ה-26)",
    "{n} locality pages requested": "{n} דפי יישובים נדרשו",
    "Locality-summed valid votes vs official": "קולות כשרים ביישובים לעומת הרשמי",
    "{summed} summed from locality pages vs {official} official.":
        "{summed} מסוכמים מדפי היישובים לעומת {official} רשמיים.",
    "Official turnout / threshold": "אחוז הצבעה / אחוז חסימה רשמיים",
    "Locality pages cover {summed} of {official} official valid votes; the remainder "
    "are double-envelope votes that the site only counts nationally. Tests 2-3 use locality sums "
    "(the only absolute counts available for both elections); Tests 4-6 default to the official "
    "national %.":
        "דפי היישובים מכסים {summed} מתוך {official} קולות כשרים רשמיים; היתר הם קולות במעטפות כפולות "
        "שהאתר סופר רק ברמה הארצית. מבחנים 2-3 משתמשים בסכומי היישובים (המספרים המוחלטים היחידים הזמינים "
        "לשתי הבחירות); מבחנים 4-6 משתמשים כברירת מחדל באחוזים הארציים הרשמיים.",
    "Localities only in the 25th: {a}; only in the 26th: {b} (excluded from the paired test).":
        "יישובים שקיימים רק בכנסת ה-25: {a}; רק בכנסת ה-26: {b} (מוחרגים מהמבחן המזווג).",
    "Poll extraction check": "בדיקת חילוץ הנתונים מהסקרים",
    "File": "קובץ", "Date": "תאריך", "N (respondents)": "N (משיבים)",
    "Seats on passing lists": "מנדטים לרשימות שעברו", "Seats on failed lists": "מנדטים לרשימות שלא עברו",
    "Undecided %": "מתלבטים %", "Status": "סטטוס",
    "Channel 13 publishes only per-sector, unweighted percentages, so its national result is "
    "mandates only; its N (2,048) is inflated by over-sampling Arab and Haredi respondents.":
        "ערוץ 13 מפרסם רק אחוזים לא משוקללים לפי מגזר, ולכן התוצאה הארצית שלו היא מנדטים בלבד; גודל "
        "המדגם שלו (2,048) מנופח עקב דגימת יתר של משיבים ערבים וחרדים.",
    "True result, by basis": "התוצאה האמיתית, לפי בסיס",
    "Official national % (renormalized)": "אחוז ארצי רשמי (מנורמל)",
    "Locality-summed (renormalized)": "סכום יישובים (מנורמל)",
    "Final seats": "מנדטים סופיים", "Seat share %": "חלק המנדטים %",
    # --- Shared stats vocabulary -----------------------------------------------------------------
    "negligible": "זניח", "small": "קטן", "medium": "בינוני", "large": "גדול",
    "Cohen's d_z": "d_z של כהן", "Rank-biserial r": "r דו-סדרתי של דרגות",
    "Cohen's h": "h של כהן", "Cohen's w": "w של כהן", "Cramér's V": "V של קרמר",
    "Party": "מפלגה", "Test": "מבחן", "Change": "שינוי",
    "25th": "ה-25", "26th": "ה-26", "25th election": "הבחירות ה-25", "26th election": "הבחירות ה-26",
    "25th share": "חלק ב-25", "26th share": "חלק ב-26",
    "25th share %": "חלק ב-25 %", "26th share %": "חלק ב-26 %",
    "95% CI {low} to {high}": "רווח סמך 95%: {low} עד {high}",
    "yes": "כן", "no": "לא",
    # --- Test 1 ----------------------------------------------------------------------------------
    "Test 1 - Did a party gain or lose in the average city? (paired t-test / Wilcoxon)":
        "מבחן 1 - האם מפלגה התחזקה או נחלשה ביישוב הממוצע? (מבחן t מזווג / וילקוקסון)",
    "Locality-group mapping": "מיפוי קבוצות",
    "Minimum valid votes per locality (both elections)": "מינימום קולות כשרים ליישוב (בשתי הבחירות)",
    "Auto (by normality)": "אוטומטי (לפי נורמליות)",
    "Paired t-test": "מבחן t מזווג",
    "Wilcoxon signed-rank": "מבחן וילקוקסון (דרגות מסומנות)",
    "Mapping: {note}": "מיפוי: {note}",
    "Matched localities": "יישובים מותאמים",
    "Mean change per locality": "שינוי ממוצע ליישוב",
    "**{method}**: statistic = {stat}, {sig}. The other test gives p = {other}. "
    "Normality: Shapiro-Wilk p = {shapiro}, skew = {skew}, excess kurtosis = {kurt}.":
        "**{method}**: סטטיסטי = {stat}, {sig}. המבחן השני נותן p = {other}. נורמליות: שפירו-וילק "
        "p = {shapiro}, אסימטריה = {skew}, גבוהנות עודפת = {kurt}.",
    "Auto-selection uses Shapiro-Wilk; with hundreds of localities it rejects normality "
    "even for mild deviations, so also inspect the histogram, Q-Q plot and skew.":
        "הבחירה האוטומטית מתבססת על שפירו-וילק; עם מאות יישובים הוא דוחה נורמליות גם בסטיות קלות, ולכן "
        "כדאי לבדוק גם את ההיסטוגרמה, תרשים Q-Q והאסימטריה.",
    "Shapiro-Wilk was run on a random subsample of 5,000 localities.":
        "מבחן שפירו-וילק הורץ על תת-מדגם אקראי של 5,000 יישובים.",
    "Every locality counts equally here, so tiny villages weigh as much as Tel Aviv. "
    "This is the typical-locality shift, not the national swing (see Test 3).":
        "כאן כל יישוב נחשב באותו משקל, ולכן כפר קטן שווה לתל אביב. זהו השינוי ביישוב טיפוסי ולא המהפך "
        "הארצי (ראו מבחן 3).",
    "Change in vote share per locality (26th - 25th)": "שינוי בחלק הקולות ליישוב (ה-26 פחות ה-25)",
    "Q-Q plot against the normal distribution": "תרשים Q-Q מול ההתפלגות הנורמלית",
    "Largest local changes": "השינויים המקומיים הגדולים ביותר",
    "Locality": "יישוב", "Valid votes (25th)": "קולות כשרים (ה-25)", "Valid votes (26th)": "קולות כשרים (ה-26)",
    "Share (25th)": "חלק (ה-25)", "Share (26th)": "חלק (ה-26)", "Change (pp)": "שינוי (נק' אחוז)",
    "Test 1 could not be computed: {error}": "לא ניתן לחשב את מבחן 1: {error}",
    # --- Test 2 ----------------------------------------------------------------------------------
    "Test 2 - Did the national voting map change? (χ² test of homogeneity)":
        "מבחן 2 - האם מפת ההצבעה הארצית השתנתה? (מבחן חי בריבוע להומוגניות)",
    "Votes in table": "קולות בטבלה", "χ² (df)": "χ² (דרגות חופש)",
    "**With N = {n} votes, p will be ≈ 0 for almost any change - read Cramér's V instead.** "
    "V = {v} is a **{label}** effect (thresholds 0.1 / 0.3 / 0.5).":
        "**עם N = {n} קולות, p יהיה כמעט 0 כמעט לכל שינוי - יש להתבונן ב-V של קרמר.** "
        "V = {v} הוא אפקט **{label}** (ספים: 0.1 / 0.3 / 0.5).",
    "Categories are every list on the ballot in either election (union); a list absent from one "
    "election has a zero count there. Counts are locality sums (no double envelopes). "
    "Much of the measured shift comes from lists that exist in only one election (new parties, "
    "mergers and splits), which mechanically inflates V - the residuals show where.":
        "הקטגוריות הן כל הרשימות שהופיעו בפתק באחת משתי הבחירות (איחוד); לרשימה שלא התמודדה באחת הבחירות "
        "יש שם ספירה אפס. הספירות הן סכומי יישובים (ללא מעטפות כפולות). חלק גדול מהשינוי הנמדד נובע "
        "מרשימות שקיימות רק באחת הבחירות (מפלגות חדשות, איחודים ופיצולים), מה שמנפח את V באופן מכני - "
        "השאריות מראות היכן.",
    "Standardized residuals, 26th election (blue = more votes than if nothing changed)":
        "שאריות מתוקנות, הבחירות ה-26 (כחול = יותר קולות מאילו דבר לא השתנה)",
    "Standardized residual": "שארית מתוקנת",
    "{n} cells have expected count < 5 (tiny lists); results are dominated by the large lists.":
        "ב-{n} תאים הספירה הצפויה קטנה מ-5 (רשימות זעירות); התוצאות נשלטות על ידי הרשימות הגדולות.",
    "Test 2 could not be computed: {error}": "לא ניתן לחשב את מבחן 2: {error}",
    # --- Test 3 ----------------------------------------------------------------------------------
    "Test 3 - Did one party's national support change? (two-proportion z-test)":
        "מבחן 3 - האם התמיכה הארצית במפלגה אחת השתנתה? (מבחן Z להפרש פרופורציות)",
    "{votes} of {valid} valid votes": "{votes} מתוך {valid} קולות כשרים",
    "**N is in the millions ({n25} and {n26} votes), so almost every change is 'significant'.** "
    "Judge the change by its size: h = {h} is **{label}** (thresholds 0.2 / 0.5 / 0.8).":
        "**N הוא במיליונים ({n25} ו-{n26} קולות), ולכן כמעט כל שינוי הוא 'מובהק'.** "
        "יש לשפוט את השינוי לפי גודלו: h = {h} הוא אפקט **{label}** (ספים: 0.2 / 0.5 / 0.8).",
    "Counts are locality sums, so each election excludes double-envelope votes; shares are of "
    "valid votes.":
        "הספירות הן סכומי יישובים, ולכן בכל בחירות חסרים קולות במעטפות כפולות; החלקים הם מתוך הקולות הכשרים.",
    "{party}: share of valid votes": "{party}: חלק מהקולות הכשרים",
    "Share of valid votes (%)": "חלק מהקולות הכשרים (%)",
    "Test 3 could not be computed: {error}": "לא ניתן לחשב את מבחן 3: {error}",
    # --- Test 4 ----------------------------------------------------------------------------------
    "Test 4 - Did each channel's map match reality? (χ² goodness of fit)":
        "מבחן 4 - האם המפה של כל ערוץ תאמה את המציאות? (חי בריבוע להתאמה)",
    "Truth: {basis}. Poll: seats ÷ seats on lists that passed the threshold, times N respondents. "
    "Both restricted to the 11 lists that passed.":
        "אמת: {basis}. סקר: מנדטים ÷ סך המנדטים של הרשימות שעברו את אחוז החסימה, כפול N משיבים. "
        "שניהם מוגבלים ל-11 הרשימות שעברו.",
    "N": "N", "χ²": "χ²", "Effective N": "N אפקטיבי", "df": "דרגות חופש", "p-value": "ערך p", "Effect": "אפקט",
    "Reject H0": "דחיית H0",
    "H0: the poll's distribution equals the true one. Cohen's w: 0.1 small, 0.3 medium, "
    "0.5 large. Seat counts are coarse (1 seat = 0.83 pp), so even a perfect poll shows "
    "some χ².":
        "H0: התפלגות הסקר שווה לאמיתית. w של כהן: 0.1 קטן, 0.3 בינוני, 0.5 גדול. ספירת המנדטים גסה "
        "(מנדט אחד = 0.83 נק' אחוז), ולכן גם סקר מושלם יראה χ² מסוים.",
    "Channel detail": "פירוט לפי ערוץ",
    "{n} cells have expected counts below 5; the χ² approximation is weak.":
        "ב-{n} תאים הספירה הצפויה נמוכה מ-5; קירוב החי בריבוע חלש.",
    "{channel} poll": "הסקר של {channel}",
    "True result": "התוצאה האמיתית",
    "{channel}: poll vs true share (among lists that passed)":
        "{channel}: חלק בסקר מול החלק האמיתי (בין הרשימות שעברו)",
    "observed": "נצפה", "expected": "צפוי", "poll_share": "חלק בסקר", "true_share": "חלק אמיתי",
    "std_residual": "שארית מתוקנת",
    "No channel has a usable sample size.": "לאף ערוץ אין גודל מדגם שמיש.",
    "Test 4 could not be computed: {error}": "לא ניתן לחשב את מבחן 4: {error}",
    # --- Test 5 ----------------------------------------------------------------------------------
    "Test 5 - Did a channel miss one party? (one-sample z-test for a proportion)":
        "מבחן 5 - האם ערוץ החטיא מפלגה אחת? (מבחן Z לפרופורציה במדגם אחד)",
    "No poll could be read.": "לא ניתן היה לקרוא אף סקר.",
    "Poll": "סקר", "True": "אמת", "Poll - true": "סקר פחות אמת",
    "{n} seats": "{n} מנדטים",
    "±{moe} 95% margin at the true share": "±{moe} שולי טעות 95% סביב החלק האמיתי",
    "z = {z}, {sig}. Wilson 95% CI for the poll share: {low} to {high} (effective N = {n}).":
        "z = {z}, {sig}. רווח סמך וילסון 95% לחלק בסקר: {low} עד {high} (N אפקטיבי = {n}).",
    "True ±95% margin": "אמת ± שולי טעות 95%",
    "{channel}: every list, with the sampling margin around the true share":
        "{channel}: כל הרשימות, עם שולי הדגימה סביב החלק האמיתי",
    "Test 5 could not be computed: {error}": "לא ניתן לחשב את מבחן 5: {error}",
    # --- Test 6 ----------------------------------------------------------------------------------
    "Test 6 - Which channel was most accurate? (MAE, RMSE and paired comparison)":
        "מבחן 6 - איזה ערוץ היה המדויק ביותר? (MAE, RMSE והשוואה מזווגת)",
    "MAE (pp)": "MAE (נק' אחוז)", "RMSE (pp)": "RMSE (נק' אחוז)",
    "Max |error| (pp)": "שגיאה מקסימלית בערך מוחלט (נק' אחוז)", "Parties": "מפלגות",
    "Error across the 11 lists that passed (lower is better)": "שגיאה בין 11 הרשימות שעברו (נמוך יותר = טוב יותר)",
    "Error (percentage points)": "שגיאה (נקודות אחוז)",
    "Signed error: poll - truth (pp)": "שגיאה מסומנת: סקר פחות אמת (נק' אחוז)",
    "Is one channel significantly better than another?": "האם ערוץ אחד טוב מובהקות מערוץ אחר?",
    "Channel A": "ערוץ א'", "Channel B": "ערוץ ב'",
    "Pick two different channels.": "בחרו שני ערוצים שונים.",
    "Mean |error| {channel}": "ממוצע |שגיאה| {channel}",
    "{channel} had the smaller errors on average": "ל{channel} היו שגיאות קטנות יותר בממוצע",
    ", but the difference is not statistically distinguishable": ", אך ההבדל אינו מובהק סטטיסטית",
    "Paired t-test on {n} lists: t = {tstat}, {sig}; Wilcoxon p = {pw}. {verdict}.":
        "מבחן t מזווג על {n} רשימות: t = {tstat}, {sig}; וילקוקסון p = {pw}. {verdict}.",
    "All channel pairs (Holm-adjusted paired t-test p-values)": "כל זוגות הערוצים (ערכי p של t מזווג, מתוקנים בהולם)",
    "Only about 11 lists per pair, errors are not independent (shares sum to 100%), and polls "
    "were fielded on different dates. Treat p-values as indicative, not definitive.":
        "יש רק כ-11 רשימות לכל זוג, השגיאות אינן בלתי תלויות (החלקים מסתכמים ל-100%), והסקרים נערכו "
        "בתאריכים שונים. יש להתייחס לערכי p כאל אינדיקציה בלבד.",
    "Seat forecast vs final seats": "תחזית מנדטים מול מנדטים סופיים",
    "Seat MAE": "MAE במנדטים", "Seats given to failed lists": "מנדטים שניתנו לרשימות שלא עברו",
    "Seat-level error is not renormalized, so a channel is penalized when it gave seats to "
    "lists that did not pass.":
        "שגיאת המנדטים אינה מנורמלת, ולכן ערוץ נענש כשהוא נתן מנדטים לרשימות שלא עברו.",
    "Test 6 could not be computed: {error}": "לא ניתן לחשב את מבחן 6: {error}",
    # --- Plot text -------------------------------------------------------------------------------
    "mean": "ממוצע", "localities": "יישובים", "Localities": "יישובים",
    "theoretical": "תיאורטי", "Normal reference": "התפלגות נורמלית",
    "Observed change (pp)": "שינוי נצפה (נק' אחוז)", "Theoretical normal quantiles": "אחוזונים נורמליים תיאורטיים",
    "row better": "השורה מדויקת יותר", "column better": "העמודה מדויקת יותר", "Holm p": "p לאחר תיקון הולם",
    # --- Statistical method names / labels from knesset_stats ------------------------------------
    "t-test": "מבחן t", "wilcoxon": "וילקוקסון",
    # --- Continuity groups (knesset_stats.parties) -----------------------------------------------
    "Likud": "הליכוד", "Shas": "ש\"ס", "United Torah Judaism": "יהדות התורה",
    "Yisrael Beiteinu": "ישראל ביתנו", "Ra'am": "רע\"ם",
    "Religious Zionism + Otzma Yehudit (merged)": "הציונות הדתית + עוצמה יהודית (מאוחד)",
    "Democrats vs Labor + Meretz (merged)": "הדמוקרטים מול העבודה + מרצ (מאוחד)",
    "Joint List vs Hadash-Ta'al + Balad (merged)": "הרשימה המשותפת מול חד\"ש-תע\"ל + בל\"ד (מאוחד)",
    "In the 25th Knesset Otzma Yehudit ran jointly on the Religious Zionism list (zipper "
    "arrangement), so only one combined count exists. The 26th lists are summed to match.":
        "בכנסת ה-25 עוצמה יהודית רצה במשותף ברשימת הציונות הדתית (הסדר רוכסן), ולכן קיימת ספירה משותפת "
        "אחת בלבד. רשימות הכנסת ה-26 מסוכמות בהתאם.",
    "The Democrats are the 26th-Knesset merger of Labor and Meretz; the 25th counts are summed.":
        "הדמוקרטים הם איחוד של העבודה ומרצ בכנסת ה-26; ספירות הכנסת ה-25 מסוכמות.",
    "The Joint List re-united Hadash-Ta'al and Balad in the 26th Knesset; the 25th counts are summed.":
        "הרשימה המשותפת איחדה מחדש את חד\"ש-תע\"ל ובל\"ד בכנסת ה-26; ספירות הכנסת ה-25 מסוכמות.",
}

HE.update(HE_EXPLANATIONS)


def make_translator(lang: str) -> Callable[[str], str]:
    """Return ``t(text)``: identity for English, table lookup (English fallback) for Hebrew."""
    if lang != "he":
        return lambda text: text

    def translate(text: str) -> str:
        if not isinstance(text, str):
            return text
        translated = HE.get(text)
        if translated is None:
            if text.strip():
                MISSING.add(text)
            return text
        return translated

    return translate


def rtl_css() -> str:
    """CSS that flips the page to right-to-left while keeping charts and tables left-to-right."""
    return """
<style>
.stApp, [data-testid="stSidebar"] { direction: rtl; }
[data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"],
[data-testid="stMetric"], [data-testid="stAlert"], [data-testid="stWidgetLabel"] { text-align: right; }
[data-testid="stMarkdownContainer"] ul, [data-testid="stMarkdownContainer"] ol,
[data-testid="stMarkdownContainer"] li, [data-testid="stExpander"] details { direction: rtl; text-align: right; }
[data-testid="stMarkdownContainer"] ul, [data-testid="stMarkdownContainer"] ol { padding-inline-start: 1.5rem; }
/* Dropdown lists render in a portal outside .stApp, so they do not inherit the direction. */
[data-testid="stSelectboxVirtualDropdown"], [data-testid="stSelectboxVirtualDropdown"] [role="listbox"],
[data-testid="stSelectboxVirtualDropdown"] [role="option"], [role="listbox"], [role="listbox"] [role="option"],
[data-baseweb="popover"] { direction: rtl; text-align: right; }
[data-testid="stPlotlyChart"], [data-testid="stDataFrame"], [data-testid="stSlider"] { direction: ltr; }
</style>
"""


RTL_LOCALE_LANGUAGES = {"he", "iw", "ar", "fa", "ur"}


def is_rtl_locale(locale: str | None) -> bool:
    """True when the browser locale (e.g. 'he-IL') is a right-to-left language."""
    if not locale:
        return False
    return locale.replace("_", "-").split("-")[0].lower() in RTL_LOCALE_LANGUAGES


def rtl_slider_css() -> str:
    """CSS for sliders under an RTL browser locale.

    Streamlit (React Aria) mirrors slider thumbs in JavaScript for RTL locales, so the first option sits on
    the right. The caller reverses the options to keep values ascending left-to-right; the tick bar (min/max
    labels) must be laid out right-to-left to match the thumb track. The filled track is fixed per slider by
    slider_fill_css.
    """
    return """
<style>
[data-testid="stSliderTickBar"] { direction: rtl; }
</style>
"""


def slider_fill_css(key: str, options: list, primary: str = "#ff4b4b") -> str:
    """CSS that draws the filled track of a mirrored select slider from its left edge up to the thumb.

    Streamlit paints the fill as a left-to-right gradient from the unmirrored percent, so under an RTL locale
    it sits on the wrong side. The thumb's hidden range input carries aria-valuetext = str(option), which
    lets CSS (:has) pick the fill length for the current value, including live while dragging. `options` must
    be in the order passed to st.select_slider (i.e. already reversed). ".efbyxod5" is Streamlit's emotion
    class for the fill element (verified on streamlit 1.66).
    """
    last = max(len(options) - 1, 1)
    rules = []
    for index, option in enumerate(options):
        thumb_left = 100.0 * (1.0 - index / last)
        rules.append(
            f'.st-key-{key}:has(input[aria-valuetext="{option}"]) .efbyxod5 {{ background: linear-gradient('
            f"to right, {primary} {thumb_left:.3f}%, rgba(151, 166, 195, 0.25) {thumb_left:.3f}%) !important; }}"
        )
    return "<style>" + "\n".join(rules) + "</style>"

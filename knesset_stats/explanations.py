"""Plain-language explanations of each test and of the statistical terms used in its tab.

Every text is an ``(English, Hebrew)`` pair. ``HE_EXPLANATIONS`` maps the English text to the Hebrew one so
that ``i18n`` can merge it into its translation table. Basic terms (mean, standard deviation, p-value) are
deliberately not explained.
"""
from __future__ import annotations

Pair = tuple[str, str]

EXPANDER_TITLE: Pair = ("What is this test? Terms explained", "מהו המבחן? הסבר על המונחים")

PP: tuple[Pair, Pair] = (
    ("Percentage points (pp)", "נקודות אחוז (pp)"),
    ("The plain difference between two percentages: going from 10% to 12% is +2 pp (not +20%).",
     "ההפרש הפשוט בין שני אחוזים: מעבר מ-10% ל-12% הוא +2 נקודות אחוז (ולא +20%)."),
)
CI: tuple[Pair, Pair] = (
    ("95% confidence interval (CI)", "רווח סמך של 95%"),
    ("A range of plausible values for the true quantity. If the study were repeated many times, about 95% of "
     "such ranges would contain the true value.",
     "טווח של ערכים סבירים לגודל האמיתי. אילו המחקר היה חוזר על עצמו פעמים רבות, כ-95% מהטווחים כאלה "
     "היו מכילים את הערך האמיתי."),
)
NULL: tuple[Pair, Pair] = (
    ("Null hypothesis (H0)", "השערת האפס (H0)"),
    ("The 'nothing happened' assumption the test tries to refute, e.g. 'the party's share did not change'. "
     "A small p-value is evidence against it.",
     "ההנחה ש'לא קרה כלום' שהמבחן מנסה להפריך, למשל 'חלקה של המפלגה לא השתנה'. ערך p קטן הוא ראיה נגדה."),
)
EFFECT_SIZE: tuple[Pair, Pair] = (
    ("Effect size", "גודל אפקט"),
    ("How big the difference is, regardless of sample size. With very large samples almost any difference is "
     "'significant', so the effect size tells whether it also matters in practice.",
     "עד כמה ההבדל גדול, בלי קשר לגודל המדגם. במדגמים גדולים מאוד כמעט כל הבדל הוא 'מובהק', ולכן גודל "
     "האפקט אומר אם הוא גם משמעותי בפועל."),
)
DESIGN_EFFECT: tuple[Pair, Pair] = (
    ("Design effect and effective N", "אפקט תכנון (design effect) ומדגם אפקטיבי"),
    ("Polls are not perfect random samples (weighting, online panels), which makes them less precise than "
     "their N suggests. Effective N = N ÷ design effect; a design effect of 2 means the poll is as precise as "
     "a random sample half its size. Set it in the sidebar.",
     "סקרים אינם מדגמים אקראיים מושלמים (שקלול, פאנלים מקוונים), ולכן הם פחות מדויקים ממה שגודל המדגם "
     "N מרמז. N אפקטיבי = N ÷ אפקט התכנון; אפקט תכנון 2 פירושו שהסקר מדויק כמו מדגם אקראי בחצי מהגודל. "
     "ניתן לקבוע אותו בסרגל הצד."),
)

# key -> (what the test asks, [(term, definition), ...])
EXPLAINERS: dict[str, tuple[Pair, list[tuple[Pair, Pair]]]] = {
    "test1": (
        ("Takes a party's share in every locality in the 25th and in the 26th election and looks at the "
         "difference. The test asks whether the typical difference across localities is different from zero. "
         "Every locality counts equally, whatever its size.",
         "לוקח את חלקה של מפלגה בכל יישוב בבחירות ה-25 וב-26 ובוחן את ההפרש. המבחן שואל אם ההפרש הטיפוסי "
         "בין היישובים שונה מאפס. כל יישוב נחשב באותה מידה, בלי קשר לגודלו."),
        [
            (("Paired test", "מבחן זוגות (paired)"),
             ("Each locality is compared with itself in the two elections. This removes the differences "
              "between localities (big or small, left or right) and leaves only the change.",
              "כל יישוב מושווה לעצמו בשתי הבחירות. כך מסירים את ההבדלים בין היישובים (גדולים או קטנים, "
              "ימניים או שמאליים) ונשאר רק השינוי.")),
            (("Paired t-test", "מבחן t לזוגות"),
             ("Tests whether the average of the per-locality differences is zero. Works best when the "
              "differences are roughly bell-shaped.",
              "בודק אם ממוצע ההפרשים בין היישובים הוא אפס. עובד הכי טוב כשההפרשים בקירוב בצורת פעמון.")),
            (("Wilcoxon signed-rank test", "מבחן וילקוקסון לדרגות מסומנות"),
             ("A rank-based alternative that does not assume a bell shape and is less affected by a few "
              "extreme localities. It checks whether changes lean more in one direction than the other.",
              "חלופה מבוססת דרגות שאינה מניחה צורת פעמון ופחות רגישה למעט יישובים קיצוניים. היא בודקת אם "
              "השינויים נוטים לכיוון אחד יותר מהאחר.")),
            (("Shapiro-Wilk, skew, excess kurtosis", "שפירו-וילק, אסימטריה (skew), גבנוניות עודפת"),
             ("Checks of whether the differences look bell-shaped. Shapiro-Wilk: a small p means they do not. "
              "Skew: 0 is symmetric, positive means a long tail of large positive values. Excess kurtosis: "
              "0 equals a bell curve, positive means heavier tails (more extreme outliers).",
              "בדיקות אם ההפרשים נראים כמו פעמון. שפירו-וילק: p קטן אומר שלא. אסימטריה: 0 היא סימטרית, ערך "
              "חיובי פירושו זנב ארוך של ערכים חיוביים גדולים. גבנוניות עודפת: 0 כמו פעמון, ערך חיובי פירושו "
              "זנבות כבדים יותר (יותר חריגים קיצוניים).")),
            (("Cohen's d_z", "d_z של כהן"),
             ("Effect size for paired data: the mean difference divided by the standard deviation of the "
              "differences. Rough guide: 0.2 small, 0.5 medium, 0.8 large.",
              "גודל אפקט לנתונים זוגיים: ממוצע ההפרשים חלקי סטיית התקן של ההפרשים. אמות מידה גסות: 0.2 קטן, "
              "0.5 בינוני, 0.8 גדול.")),
            (("Rank-biserial r", "מתאם דרגות ביסריאלי (r)"),
             ("Effect size for the Wilcoxon test, from -1 to +1: the balance between upward and downward "
              "changes (weighted by rank). 0 means no tendency in either direction.",
              "גודל אפקט למבחן וילקוקסון, בין -1 ל-+1: האיזון בין שינויים כלפי מעלה וכלפי מטה (משוקלל לפי "
              "דרגה). 0 פירושו שאין נטייה לאף כיוון.")),
            CI, PP,
        ],
    ),
    "test2": (
        ("Compares the national distribution of votes across all lists in the two elections and asks whether "
         "the two distributions are the same.",
         "משווה את התפלגות הקולות הארצית בין כל הרשימות בשתי הבחירות ושואל אם שתי ההתפלגויות זהות."),
        [
            (("χ² (chi-square) test of homogeneity", "מבחן χ² (חי בריבוע) להומוגניות"),
             ("Compares observed vote counts with the counts expected if both elections had the same "
              "distribution. The larger the gaps, the larger χ².",
              "משווה את ספירות הקולות שנצפו לספירות שהיו צפויות אילו בשתי הבחירות הייתה אותה התפלגות. "
              "ככל שהפערים גדולים יותר, χ² גדול יותר.")),
            (("df (degrees of freedom)", "df (דרגות חופש)"),
             ("The number of values that can vary freely. Here: the number of lists minus 1. It sets which "
              "χ² distribution the p-value is read from.",
              "מספר הערכים שיכולים להשתנות בחופשיות. כאן: מספר הרשימות פחות 1. הוא קובע מאיזו התפלגות χ² "
              "נקרא ערך p.")),
            (("Cramér's V", "V של קרמר"),
             ("Effect size for χ² tests, from 0 (identical distributions) to 1 (completely different). "
              "Rough guide: 0.1 small, 0.3 medium, 0.5 large.",
              "גודל אפקט למבחני χ², בין 0 (התפלגויות זהות) ל-1 (שונות לגמרי). אמות מידה גסות: 0.1 קטן, "
              "0.3 בינוני, 0.5 גדול.")),
            (("Standardized residual", "שארית מתוקננת"),
             ("How far one list's count is from what was expected, measured in standard-error units. Around "
              "±2 or beyond marks the lists that drive the change; the sign shows the direction.",
              "עד כמה הספירה של רשימה אחת רחוקה ממה שצפוי, ביחידות של שגיאת תקן. בערך ±2 ומעלה מסמן את "
              "הרשימות שמניעות את השינוי; הסימן מראה את הכיוון.")),
            (("Expected count < 5", "ספירה צפויה קטנה מ-5"),
             ("The χ² approximation is unreliable for cells with fewer than 5 expected votes (very small "
              "lists), so those cells are flagged.",
              "קירוב ה-χ² אינו אמין בתאים עם פחות מ-5 קולות צפויים (רשימות קטנות מאוד), ולכן תאים כאלה "
              "מסומנים.")),
            EFFECT_SIZE, NULL,
        ],
    ),
    "test3": (
        ("Takes one party's share of the valid votes in each election and asks whether the share changed "
         "nationally.",
         "לוקח את חלקה של מפלגה אחת מהקולות התקפים בכל בחירות ושואל אם חלקה הארצי השתנה."),
        [
            (("Two-proportion z-test", "מבחן Z להפרש פרופורציות"),
             ("Compares two proportions (the party's share in the 25th and in the 26th election). z is the "
              "difference divided by its standard error; |z| above about 2 is significant at the 5% level.",
              "משווה שתי פרופורציות (חלק המפלגה בבחירות ה-25 וה-26). z הוא ההפרש חלקי שגיאת התקן שלו; "
              "|z| מעל כ-2 מובהק ברמת 5%.")),
            (("Cohen's h", "h של כהן"),
             ("Effect size for the difference between two proportions. It uses a transformation that makes "
              "the same gap count more near 0% than near 50%. Rough guide: 0.2 small, 0.5 medium, 0.8 large.",
              "גודל אפקט להפרש בין שתי פרופורציות. הוא משתמש בהמרה שגורמת לאותו פער להיחשב גדול יותר ליד 0% "
              "מאשר ליד 50%. אמות מידה גסות: 0.2 קטן, 0.5 בינוני, 0.8 גדול.")),
            EFFECT_SIZE, CI, PP,
        ],
    ),
    "test4": (
        ("Treats each channel's seat forecast as a distribution of voters and asks whether it differs from the "
         "true result across the 11 lists that passed the threshold.",
         "מתייחס לתחזית המנדטים של כל ערוץ כהתפלגות של מצביעים ושואל אם היא שונה מהתוצאה האמיתית בין 11 "
         "הרשימות שעברו את אחוז החסימה."),
        [
            (("χ² goodness-of-fit test", "מבחן χ² להתאמה"),
             ("Compares the counts implied by the poll with the counts expected if the poll matched the true "
              "result exactly. A large χ² means the poll's map does not fit reality.",
              "משווה את הספירות שנובעות מהסקר לספירות שהיו צפויות אילו הסקר תאם בדיוק את התוצאה האמיתית. "
              "χ² גדול פירושו שמפת הסקר אינה מתאימה למציאות.")),
            (("Cohen's w", "w של כהן"),
             ("Effect size for goodness of fit: the size of the gap between the poll and the truth, "
              "independent of N. Rough guide: 0.1 small, 0.3 medium, 0.5 large.",
              "גודל אפקט להתאמה: גודל הפער בין הסקר לאמת, בלי תלות ב-N. אמות מידה גסות: 0.1 קטן, "
              "0.3 בינוני, 0.5 גדול.")),
            (("Reject H0", "דחיית H0"),
             ("'Yes' means the poll differs from the true result by more than sampling noise alone would "
              "explain, at the chosen significance level α.",
              "'כן' פירושו שהסקר שונה מהתוצאה האמיתית יותר ממה שרעש דגימה לבדו מסביר, ברמת המובהקות α "
              "שנבחרה.")),
            (("Seat granularity", "גסות המנדטים"),
             ("A poll reports whole seats (1 seat = 0.83 pp), so even a perfect poll shows some χ² from "
              "rounding alone.",
              "סקר מדווח על מנדטים שלמים (מנדט אחד = 0.83 נקודות אחוז), ולכן גם סקר מושלם מראה מעט χ² "
              "מעיגול בלבד.")),
            DESIGN_EFFECT, NULL,
        ],
    ),
    "test5": (
        ("Picks one channel and one party and asks whether the poll's share for that party is consistent with "
         "the true share, given the poll's sampling error.",
         "בוחר ערוץ אחד ומפלגה אחת ושואל אם חלקה של המפלגה בסקר עקבי עם חלקה האמיתי, בהינתן שגיאת הדגימה "
         "של הסקר."),
        [
            (("One-sample z-test for a proportion", "מבחן Z לפרופורציה במדגם אחד"),
             ("Compares one observed proportion (the poll) with a known value (the true result). z measures "
              "how many standard errors apart they are.",
              "משווה פרופורציה נצפית אחת (הסקר) לערך ידוע (התוצאה האמיתית). z מודד בכמה שגיאות תקן הם רחוקים.")),
            (("Margin of error", "שולי טעות"),
             ("The ± range around the true share within which a poll of this size would land 95% of the time "
              "by chance alone.",
              "טווח ה-± סביב החלק האמיתי שבו סקר בגודל כזה היה נופל ב-95% מהמקרים רק במקרה.")),
            (("Wilson confidence interval", "רווח סמך של ווילסון"),
             ("A 95% interval for a proportion that stays reliable for small shares and small samples, "
              "unlike the simple 'share ± margin' formula.",
              "רווח של 95% לפרופורציה שנשאר אמין גם לחלקים קטנים ולמדגמים קטנים, בניגוד לנוסחה הפשוטה "
              "'חלק ± שולי טעות'.")),
            (("Cohen's h", "h של כהן"),
             ("Effect size for the gap between two proportions. Rough guide: 0.2 small, 0.5 medium, "
              "0.8 large.",
              "גודל אפקט לפער בין שתי פרופורציות. אמות מידה גסות: 0.2 קטן, 0.5 בינוני, 0.8 גדול.")),
            DESIGN_EFFECT, PP,
        ],
    ),
    "test6": (
        ("Measures how far each channel's forecast was from the true result across the lists that passed, "
         "ranks the channels, and tests whether the differences between channels are real.",
         "מודד עד כמה תחזית כל ערוץ הייתה רחוקה מהתוצאה האמיתית בין הרשימות שעברו, מדרג את הערוצים ובודק אם "
         "ההבדלים בין הערוצים אמיתיים."),
        [
            (("MAE (mean absolute error)", "MAE (שגיאה מוחלטת ממוצעת)"),
             ("The average size of the error per list, ignoring direction. Easy to read: an MAE of 0.5 pp "
              "means the channel was off by half a percentage point on average.",
              "גודל השגיאה הממוצע לכל רשימה, בלי קשר לכיוון. קל לקריאה: MAE של 0.5 נקודות אחוז פירושו "
              "שהערוץ טעה בממוצע בחצי נקודת אחוז.")),
            (("RMSE (root mean squared error)", "RMSE (שורש השגיאה הריבועית הממוצעת)"),
             ("Like MAE, but squares errors before averaging, so one big miss counts much more than several "
              "small ones. RMSE well above MAE signals a few large misses.",
              "כמו MAE, אך מעלה את השגיאות בריבוע לפני הממוצע, כך שפספוס גדול אחד נחשב הרבה יותר מכמה "
              "קטנים. RMSE גבוה בהרבה מ-MAE מעיד על כמה פספוסים גדולים.")),
            (("Signed error", "שגיאה מסומנת"),
             ("Poll minus truth. Positive means the channel over-estimated the list, negative means it "
              "under-estimated it.",
              "סקר פחות אמת. חיובי פירושו שהערוץ העריך את הרשימה ביתר, שלילי פירושו שהעריך בחסר.")),
            (("Paired comparison of two channels", "השוואה זוגית בין שני ערוצים"),
             ("For each list, the two channels' absolute errors are compared, then a paired t-test (and a "
              "Wilcoxon test) checks whether one channel is consistently closer. Cohen's d_z is the effect "
              "size (0.2 small, 0.5 medium, 0.8 large).",
              "לכל רשימה משווים את השגיאות המוחלטות של שני הערוצים, ואז מבחן t לזוגות (ומבחן וילקוקסון) "
              "בודק אם ערוץ אחד קרוב יותר באופן עקבי. d_z של כהן הוא גודל האפקט (0.2 קטן, 0.5 בינוני, "
              "0.8 גדול).")),
            (("Holm adjustment", "תיקון הולם (Holm)"),
             ("Comparing many pairs of channels at once makes a false 'significant' result likely by chance. "
              "The Holm correction raises the p-values to account for this.",
              "השוואת הרבה זוגות ערוצים בבת אחת הופכת תוצאה 'מובהקת' שגויה לסבירה במקרה. תיקון הולם מעלה "
              "את ערכי p כדי להתחשב בכך.")),
            PP,
        ],
    ),
}


def _pairs() -> list[Pair]:
    pairs: list[Pair] = [EXPANDER_TITLE]
    for intro, terms in EXPLAINERS.values():
        pairs.append(intro)
        for term, definition in terms:
            pairs.extend([term, definition])
    return pairs


HE_EXPLANATIONS: dict[str, str] = {en: he for en, he in _pairs()}

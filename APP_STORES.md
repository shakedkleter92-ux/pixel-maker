# העלאת Pixel Maker לחנויות האפליקציות

האפליקציה כבר פועלת כ־PWA ב־https://pixelmakergrid.netlify.app/  
כדי להעלות לחנות צריך לעטוף אותה כאפליקציה native. להלן הדרכים המעשיות.

---

## 1. Android (Google Play)

### א. חשבון מפתח
- היכנסי ל־[Google Play Console](https://play.google.com/console)
- רישום חד־פעמי: **25 דולר**

### ב. בניית קובץ האפליקציה (APK/AAB)
**אפשרות מומלצת – PWA Builder (חינם):**
1. גלושי ל־[https://www.pwabuilder.com](https://www.pwabuilder.com)
2. הזיני את הכתובת: `https://pixelmakergrid.netlify.app`
3. לחצי **Start** → **Package For Stores**
4. בחרי **Android** → **Generate**  
   תקבלי קובץ ZIP עם פרויקט Android (או APK מוכן).
5. אם מתקבל פרויקט: פתחי אותו ב־Android Studio ובני **Build → Generate Signed Bundle (AAB)** להעלאה ל־Play.

**אפשרות נוספת – Bubblewrap (מתקדם):**
- [Bubblewrap](https://github.com/GoogleChromeLabs/bubblewrap) – כלי שורת פקודה שיוצר TWA (Trusted Web Activity) מהכתובת של האתר.

### ג. העלאה ל־Play
- ב־Play Console: **Create app** → מילוי פרטים (שם, תיאור, צילומי מסך, אייקון)
- **Release → Production** → העלאת קובץ AAB
- אחרי בדיקה – האפליקציה תעלה לחנות

---

## 2. iOS (App Store)

### א. דרישות
- **חשבון Apple Developer** – כ־99 דולר לשנה  
  [developer.apple.com](https://developer.apple.com)
- **Mac** עם **Xcode** (לבנייה והגשה)

### ב. בניית האפליקציה
**אפשרות 1 – PWA Builder:**
1. ב־[PWA Builder](https://www.pwabuilder.com) הזיני `https://pixelmakergrid.netlify.app`
2. **Package For Stores** → **iOS**
3. תורדי חבילה – בדרך כלל תקבלי פרויקט Xcode שצריך לפתוח ב־Mac, לבנות ולהעלות דרך Xcode/App Store Connect.

**אפשרות 2 – Capacitor (יותר שליטה):**
1. בפרויקט (בתיקייה שמכילה את האתר):
   ```bash
   npm init -y
   npm install @capacitor/core @capacitor/cli
   npx cap init "Pixel Maker" com.yourname.pixelmaker
   npm install @capacitor/ios
   npx cap add ios
   ```
2. הגדירי את תיקיית ה־web root (למשל `www` או איפה ש־index.html) ב־`capacitor.config`.
3. בנה והעתק:
   ```bash
   npx cap sync ios
   npx cap open ios
   ```
4. ב־Xcode: חתימה, בחירת מכשיר/סימולטור, **Product → Archive** ואז **Distribute App** ל־App Store.

### ג. הגשה ל־App Store
- ב־[App Store Connect](https://appstoreconnect.apple.com) יוצרים אפליקציה חדשה
- ממלאים מטא־דאטה (שם, תיאור, צילומי מסך, פרטיות)
- מעלים את ה־build מ־Xcode (או מ־Transporter)
- שולחים לבדיקה (Review)

---

## 3. טיפים חשובים

| נושא | המלצה |
|------|--------|
| **אייקון** | 1024×1024 ל־App Store, וגם גרסאות ל־Android לפי הדרישות ב־Play Console |
| **צילומי מסך** | מומלץ לכל מכשיר/גודל שמדריכים (טלפון, טאבלט) |
| **מדיניות פרטיות** | נדרשת אם יש איסוף מידע (למשל מצלמה). אפשר דף סטטי ב־Netlify עם קישור במדיניות פרטיות |
| **מצלמה (Live)** | ב־iOS/Android יש לבקש הרשאות במניפסט/Info.plist (Camera usage) – PWA Builder/Capacitor מטפלים בזה בדרך כלל כשמוסיפים את ההרשאות בהגדרות |

---

## 4. סיכום צעדים מומלצים

1. **וידוא:** האתר עובד מעולה ב־https://pixelmakergrid.netlify.app (כולל מצלמה במובייל).
2. **Android:** PWA Builder → Android package → העלאה ל־Google Play Console.
3. **iOS:** PWA Builder → iOS package, או Capacitor ב־Mac → Xcode → App Store Connect.
4. **חשבונות:** Google Play 25$, Apple Developer 99$/year.

אם תרצי, אפשר בשלב הבא להכין יחד את קובץ ה־manifest ואייקונים ספציפיים לדרישות של כל חנות.

#!/bin/bash
# نسخة احترافية لصناعة ISO نظام RoboOS باستخدام grub-mkrescue
set -e

PROJECT_NAME="RoboOS"
ISO_DIR="iso_temp"
mkdir -p $ISO_DIR/boot/grub

echo "� بدأت عملية التصنيع الاحترافية..."

# 1. تحميل النواة (Tiny Core) لو مش موجودة
if [ ! -f "vmlinuz" ]; then
    echo "⬇️ جاري تحميل النواة..."
    wget -q -O vmlinuz "http://www.tinycorelinux.net/15.x/x86/release/distribution_files/vmlinuz"
fi
if [ ! -f "core.gz" ]; then
    echo "⬇️ جاري تحميل ملفات النظام..."
    wget -q -O core.gz "http://www.tinycorelinux.net/15.x/x86/release/distribution_files/core.gz"
fi

cp vmlinuz $ISO_DIR/boot/vmlinuz
cp core.gz $ISO_DIR/boot/initrd.img

# 2. إعداد قائمة الإقلاع
cat <<EOF > $ISO_DIR/boot/grub/grub.cfg
set timeout=5
set default=0
set menu_color_normal=white/black
set menu_color_highlight=black/light-gray

menuentry "🚀 Launch RoboOS - AI Powered System" {
    linux /boot/vmlinuz quiet noswap
    initrd /boot/initrd.img
}

menuentry "🛠️ System Diagnosis" {
    linux /boot/vmlinuz quiet noswap
    initrd /boot/initrd.img
}
EOF

# 3. نسخ ملفات مشروعك
mkdir -p $ISO_DIR/roboos_data
cp -r "/mnt/c/Users/Tech Shop/Desktop/hydea/RoboOs/firmware" $ISO_DIR/roboos_data/
cp "/mnt/c/Users/Tech Shop/Desktop/hydea/RoboOs/roboos.py" $ISO_DIR/roboos_data/
cp "/mnt/c/Users/Tech Shop/Desktop/hydea/RoboOs/main.py" $ISO_DIR/roboos_data/

# 4. الصناعة النهائية باستخدام grub-mkrescue (دي الأداة الأقوى)
echo "💿 جاري دمج الملفات وصناعة الـ ISO النهائي..."
grub-mkrescue -o "/mnt/c/Users/Tech Shop/Desktop/hydea/RoboOs/RoboOS_Final.iso" $ISO_DIR

echo "----------------------------------------------------"
echo "✅ مبروك! الملف جاهز الآن تحت اسم: RoboOS_Final.iso"
echo "📍 مكانه: في المجلد الرئيسي لمشروعك."
echo "----------------------------------------------------"

#!/bin/bash
# النسخة المصلحة لصناعة ISO نظام RoboOS (v15.x)
set -e

PROJECT_NAME="RoboOS"
ISO_DIR="iso_root"
mkdir -p $ISO_DIR/boot/grub

echo "📦 تجهيز بيئة الإقلاع (Tiny Core 15.x)..."

# 1. تحميل نواة Linux المحدثة
URL_BASE="http://www.tinycorelinux.net/15.x/x86/release/distribution_files"

if [ ! -f "vmlinuz" ]; then
    echo "⬇️ تحميل vmlinuz..."
    wget -q -O vmlinuz "$URL_BASE/vmlinuz"
fi
if [ ! -f "core.gz" ]; then
    echo "⬇️ تحميل core.gz..."
    wget -q -O core.gz "$URL_BASE/core.gz"
fi

cp vmlinuz $ISO_DIR/boot/vmlinuz
cp core.gz $ISO_DIR/boot/initrd.img

# 2. إنشاء قائمة الإقلاع (GRUB)
cat <<EOF > $ISO_DIR/boot/grub/grub.cfg
set timeout=5
set default=0

menuentry "Start $PROJECT_NAME Live System" {
    linux /boot/vmlinuz quiet
    initrd /boot/initrd.img
}
EOF

# 3. نسخ ملفات RoboOS الأساسية
mkdir -p $ISO_DIR/opt/roboos
# سننسخ مجلد المشروع بالكامل ليكون متاحاً
cp -r "/mnt/c/Users/Tech Shop/Desktop/hydea/RoboOs/firmware" $ISO_DIR/opt/roboos/
cp "/mnt/c/Users/Tech Shop/Desktop/hydea/RoboOs/roboos.py" $ISO_DIR/opt/roboos/
cp "/mnt/c/Users/Tech Shop/Desktop/hydea/RoboOs/main.py" $ISO_DIR/opt/roboos/

# 4. بناء الـ ISO النهائي
echo "💿 جاري ضغط ملف الـ ISO..."
grub-mkstandalone -O i386-pc -o $ISO_DIR/boot/grub/core.img --modules="biosdisk part_msdos fat normal echo"
xorriso -as mkisofs -graft-points \
    -o "/mnt/c/Users/Tech Shop/Desktop/hydea/RoboOs/RoboOS_Live.iso" \
    -b boot/grub/i386-pc/eltorito.img \
    -no-emul-boot -boot-load-size 4 -boot-info-table \
    --grub2-boot-info --grub2-mbr /usr/lib/grub/i386-pc/boot_img \
    $ISO_DIR

echo "✅ مبروك! الملف موجود دلوقتي باسم RoboOS_Live.iso في مجلد المشروع الرئيسي."

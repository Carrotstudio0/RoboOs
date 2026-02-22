#!/bin/bash
# سكربت صناعة ISO لنظام RoboOS
# يعمل داخل بيئة Ubuntu/WSL

PROJECT_NAME="RoboOS"
ISO_DIR="iso_root"
mkdir -p $ISO_DIR/boot/grub

# 1. إنشاء قائمة الإقلاع (GRUB)
cat <<EOF > $ISO_DIR/boot/grub/grub.cfg
set timeout=5
set default=0

menuentry "Start $PROJECT_NAME Live" {
    linux /boot/vmlinuz quiet splash
    initrd /boot/initrd.img
}
EOF

# 2. جلب نواة Linux مصغرة (سنستخدم نواة Ubuntu الحالية للسرعة)
cp /boot/vmlinuz-$(uname -r) $ISO_DIR/boot/vmlinuz
cp /boot/initrd.img-$(uname -r) $ISO_DIR/boot/initrd.img

# 3. نسخ ملفات نظام RoboOS
mkdir -p $ISO_DIR/opt/roboos
cp -r /mnt/c/Users/Tech\ Shop/Desktop/hydea/RoboOs/* $ISO_DIR/opt/roboos/

# 4. بناء الـ ISO النهائي
grub-mkstandalone -O i386-pc -o $ISO_DIR/boot/grub/core.img --modules="biosdisk part_msdos fat normal echo"
xorriso -as mkisofs -graft-points \
    -b boot/grub/i386-pc/eltorito.img \
    -no-emul-boot -boot-load-size 4 -boot-info-table \
    --grub2-boot-info --grub2-mbr /usr/lib/grub/i386-pc/boot_img \
    -o /mnt/c/Users/Tech\ Shop/Desktop/hydea/RoboOs/RoboOS_Live.iso \
    $ISO_DIR

echo "✅ تم بنجاح! ملف RoboOS_Live.iso موجود الآن في المجلد الرئيسي."

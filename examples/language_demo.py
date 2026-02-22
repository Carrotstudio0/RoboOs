"""
مثال 3: برنامج اللغة المخصصة
Example 3: Custom Language Program
"""

from firmware.lang.engine import LanguageEngine

def example_language_program():
    """مثال على برنامج باللغة المخصصة"""
    
    print("\n📝 مثال 3: برنامج باللغة المخصصة")
    print("="*50)
    
    # إنشاء محرك اللغة
    engine = LanguageEngine()
    
    # برنامج احسب مجموع الأرقام
    program = """
    var sum = 0;
    var i = 1;
    
    for (var i = 1; i <= 10; i = i + 1) {
        var sum = sum + i;
    }
    
    print("المجموع من 1 إلى 10:");
    print(sum);
    """
    
    print("\nالبرنامج:")
    print("-" * 40)
    print(program)
    print("-" * 40)
    
    print("\nالنتيجة:")
    try:
        # تجميع البرنامج
        ast = engine.compile(program)
        
        # تنفيذ البرنامج
        engine.execute(ast)
        
        print(f"\nالمتغيرات المحفوظة:")
        for var_name, var_value in engine.variables.items():
            print(f"  {var_name} = {var_value}")
        
        print("\n✓ انتهى المثال")
    
    except Exception as e:
        print(f"❌ خطأ: {e}")

if __name__ == "__main__":
    example_language_program()

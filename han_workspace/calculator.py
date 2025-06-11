
def add(x, y):
    return x + y

def subtract(x, y):
    return x - y

def multiply(x, y):
    return x * y

def divide(x, y):
    if y == 0:
        return "Error: Pembagian dengan nol tidak diizinkan."
    return x / y

def calculator():
    print("Selamat datang di Kalkulator CLI!")
    print("Pilih operasi:")
    print("1. Tambah (+)")
    print("2. Kurang (-)")
    print("3. Kali (*)")
    print("4. Bagi (/)")
    print("Ketik 'exit' untuk keluar.")

    while True:
        choice = input("Masukkan pilihan (1/2/3/4/exit): ")

        if choice == 'exit':
            print("Terima kasih telah menggunakan kalkulator!")
            break

        if choice in ('1', '2', '3', '4'):
            try:
                num1 = float(input("Masukkan angka pertama: "))
                num2 = float(input("Masukkan angka kedua: "))
            except ValueError:
                print("Input tidak valid. Harap masukkan angka.")
                continue

            if choice == '1':
                print(f"{num1} + {num2} = {add(num1, num2)}")
            elif choice == '2':
                print(f"{num1} - {num2} = {subtract(num1, num2)}")
            elif choice == '3':
                print(f"{num1} * {num2} = {multiply(num1, num2)}")
            elif choice == '4':
                result = divide(num1, num2)
                print(f"{num1} / {num2} = {result}")
        else:
            print("Pilihan tidak valid. Silakan coba lagi.")

if __name__ == "__main__":
    calculator()

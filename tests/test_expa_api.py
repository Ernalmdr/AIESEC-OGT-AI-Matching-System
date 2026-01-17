from src.repositories.expa_repo import ExpaRepository


def test_api():
    repo = ExpaRepository()
    projects = repo.fetch_data(programme_id=8)  # GTa test edelim

    if projects:
        print("\n🚀 İLK PROJE DETAYLARI:")
        first = projects[0]
        print(f"Başlık: {first.title}")
        print(f"JD (İlk 100 karakter): {first.description[:100]}...")
        print(f"Arkaplanlar: {first.backgrounds}")
    else:
        print("❌ Veri çekilemedi.")


if __name__ == "__main__":
    test_api()
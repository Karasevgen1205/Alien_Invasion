import sys
import pygame
from time import sleep
from settings import Settings
from ship import Ship
from bullet import Bullet
from alien import Alien
from game_stats import GameStats
from button import Button
from scoreboard import Scoreboard


class AlienInvasion:
    
    def __init__ (self):
        pygame.init()
        self.settings = Settings()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height
        pygame.display.set_caption("Alien Invasion")
        #Создание экземпляра для хранения игровой статистики 
        #и панели результатов
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)
        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self._create_fleet()
        # Создание кнопки Play
        self.play_button = Button(self, "Play")

    def run_game(self):
        #Запуск основного цикла игры
        while True:
            self._check_events()
 
            if self.stats.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()
                self.bullets.update()
            self._update_screen()

    def _check_events(self):
    #Обрабатывает нажатия клавиш и события мыши
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_play_button(self, mouse_pos):
        """Запускает новую игру при нажатии кнопки Play"""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:
            #Сброс игровых настроек
            self.settings.initialize_dynamic_settings()
            #Сброс игровой статистики
            self.stats.reset_stats()
            self.stats.game_active = True
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()
            #Очистка списков пришельцев и снарядов
            self.aliens.empty()
            self.bullets.empty()
            #Создание нового флота и размещени коробля в центре
            self._create_fleet()
            self.ship.center_ship()
            #Указатель мыши скрывается
            pygame.mouse.set_visible(False)

    def _check_keydown_events(self, event):
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            sys.exit()    
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()

    def _check_keyup_events(self, event):
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False        

    def _fire_bullet(self):
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_bullets(self):
        #Уничтожение исчезнувших снарядов
        self.bullets.update()
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)
        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):    
        #Проверка попаданий в пришельцев. 
        #При попадании в пришельа удалить снаряд и пришельца
        collisions = pygame.sprite.groupcollide(
            self.bullets, self.aliens, True, True)

        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)
            self.sb.prep_score()
            self.sb.check_high_score()

        if not self.aliens:
            #Уничтожение  снарядов, повышение скорости и создание нового флота
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()
            #Увеличение уровня
            self.stats.level += 1
            self.sb.prep_level()

    def _update_aliens(self):
        """Проверяет, достиг ли флот края экрана и обновляет их"""
        self._check_fleet_edges()
        self.aliens.update()
        #Проверка коллизий "пришелец-корабль"
        if pygame.sprite.spritecollideany (self.ship, self.aliens):
            self._ship_hit()
        #Проверяет, добрались ли пришельцы до нижнего края экрана
        self._check_aliens_bottom()    

    def _ship_hit(self):
        """Обрабатывает столкновение коробля с пришельцами"""
        if self.stats.ships_left > 0:
            #Уменьшает количество жизней и обновляет панель счета
            self.stats.ships_left -= 1
            self.sb.prep_ships()
            #Очистка мписков пришельцев и снарядов
            self.aliens.empty()
            self.bullets.empty()
            #Создание нового флота и размещение коробля в центре
            self._create_fleet()
            self.ship.center_ship()
            #Пауза
            sleep(0.5)      
        else:
            self.stats.game_active = False
            self.pygame.mouse.set_visible(True)
            self.play_button.draw_button()
            self._check_play_button()


    def _check_aliens_bottom(self):
        """Проверяет, добрались ли пришельцы до нижнего края"""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                #Происходит тоже, что и при столкновении с кораблем
                self._ship_hit()
                break

    def _create_fleet(self):
        """Создание первого ряда пришельцев"""
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        available_space_x = self.settings.screen_width - (2 * alien_width)
        number_aliens_x = available_space_x // (2 * alien_width)    
        """Определение количества рядов помещающхся на эксран"""
        ship_height = self.ship.rect.height
        available_space_y = (self.settings.screen_height - 
            (3 * alien_height) - ship_height)
        number_rows = available_space_y // (2 * alien_height)

        """Создание флота вторжения"""
        for row_numder in range(number_rows):
            for alien_number in range(number_aliens_x):
                self._create_alien(alien_number, row_numder)

    def _create_alien(self, alien_number, row_numder):        
        """Создание пришельца и размещение его в ряду"""
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_numder
        self.aliens.add(alien)

    def _check_fleet_edges(self):
        """Реагирует на достижение края экрана пришельцем"""      
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """Опускает весь флот и меняет направление движения"""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1             

    def _update_screen(self):
        self.screen.fill(self.settings.bg_color)            
        self.ship.blitme()
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.aliens.draw(self.screen)
        #Вывод информации о счете
        self.sb.show_score()
        #Кнопка Play отображается в том случае, если игра неактивна
        if not self.stats.game_active:
            self.play_button.draw_button()

        pygame.display.flip()


if __name__ == '__main__':
    ai = AlienInvasion()
    ai.run_game()


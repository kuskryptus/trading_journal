from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, is_superuser=False, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        users_group, created = Group.objects.get_or_create(name='Users')
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        user.groups.add(users_group)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        admins_group, created = Group.objects.get_or_create(name='Administrators')
        extra_fields.setdefault('is_staff', True)
        user = self.create_user(email, username, password, **extra_fields)
        user.groups.add(admins_group)
        user.save(using=self._db)
        return user


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    onboarded = models.BooleanField(default=False)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    phone_number = models.CharField(
        _("phone number"),
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^\+?1?\d{9,15}$",
                message="Phone number must be entered in the "
                "format: '+999999999'. Up to 15 "
                "digits allowed.",
            )
        ],
    )

    birth_date = models.DateField(_("birth date"), blank=True, null=True)
    location = models.CharField(_("location"), max_length=255, blank=True)

    objects = CustomUserManager()
    timezone = models.CharField(max_length=100, blank=True)
    groups = models.ManyToManyField(
        Group,
        verbose_name=_("groups"),
        blank=True,
        help_text=_(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_name="custom_user_groups",
        related_query_name="user",
    )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_("Specific permissions for this user."),
        related_name="custom_user_permissions",
        related_query_name="user",
    )

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        return self.email

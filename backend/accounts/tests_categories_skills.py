from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from accounts.models import Role, UserRole, JobCategory, Skill, CandidateProfile, CandidateSkill, JobSkill

User = get_user_model()

class CategoriesAndSkillsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create roles
        self.superadmin_role, _ = Role.objects.get_or_create(name='SUPER_ADMIN')
        self.admin_role, _ = Role.objects.get_or_create(name='ADMIN')
        self.hr_role, _ = Role.objects.get_or_create(name='HR')
        self.candidate_role, _ = Role.objects.get_or_create(name='CANDIDATE')

        # Create Super Admin user with role='SUPER_ADMIN'
        self.superadmin_user = User.objects.create_user(
            username='superadmin_user',
            email='superadmin@tnjobz.com',
            phone_number='9876543210',
            password='password123',
            role='SUPER_ADMIN',
            is_active=True
        )

        # Create Regular Admin user with role='ADMIN'
        self.admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@tnjobz.com',
            phone_number='9876543211',
            password='password123',
            role='ADMIN',
            is_active=True
        )

        # Create Candidate user with role='CANDIDATE'
        self.candidate_user = User.objects.create_user(
            username='candidate_user',
            email='candidate@tnjobz.com',
            phone_number='9876543212',
            password='password123',
            role='CANDIDATE',
            is_active=True
        )

    # -------------------------------------------------------------------
    # 1. Authorization tests
    # -------------------------------------------------------------------
    def test_superadmin_authorization_enforced(self):
        # Anonymous request
        res = self.client.get('/accounts/admin/categories/')
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        # Candidate request
        self.client.force_authenticate(user=self.candidate_user)
        res = self.client.get('/accounts/admin/categories/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Admin request (not superadmin)
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get('/accounts/admin/categories/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Super Admin request
        self.client.force_authenticate(user=self.superadmin_user)
        res = self.client.get('/accounts/admin/categories/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    # -------------------------------------------------------------------
    # 2. Category creation, editing, sort order, and active status
    # -------------------------------------------------------------------
    def test_category_creation_and_persistence(self):
        self.client.force_authenticate(user=self.superadmin_user)

        # Create Root Category
        res = self.client.post('/accounts/admin/categories/', {
            'name': 'IT & Software',
            'description': 'Software, IT support and data roles',
            'sort_order': 10,
            'is_active': True
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        parent_id = res.data['id']
        self.assertEqual(res.data['name'], 'IT & Software')

        # Create Child Category
        res_child = self.client.post('/accounts/admin/categories/', {
            'name': 'Software Developer',
            'parent': parent_id,
            'description': 'Frontend, backend, fullstack development',
            'sort_order': 1,
            'is_active': True
        }, format='json')
        self.assertEqual(res_child.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_child.data['parent_name'], 'IT & Software')

    def test_category_duplicate_validation(self):
        self.client.force_authenticate(user=self.superadmin_user)
        JobCategory.objects.create(name='Hospitality', description='Hotel and restaurant jobs')

        # Attempt to create duplicate name with extra whitespace / different case
        res = self.client.post('/accounts/admin/categories/', {
            'name': '  hospitality  ',
            'description': 'Another description',
            'sort_order': 0,
            'is_active': True
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', res.data)

    def test_category_cycle_rejection(self):
        self.client.force_authenticate(user=self.superadmin_user)
        parent = JobCategory.objects.create(name='Engineering', description='Engineering roles')
        child = JobCategory.objects.create(name='Civil Engineering', parent=parent, description='Civil design')

        # Attempt self-parenting
        res = self.client.patch(f'/accounts/admin/categories/{parent.id}/', {
            'parent': parent.id
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempt child as parent of its own parent (cycle)
        res_cycle = self.client.patch(f'/accounts/admin/categories/{parent.id}/', {
            'parent': child.id
        }, format='json')
        self.assertEqual(res_cycle.status_code, status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------------
    # 3. Skill creation, editing, category linking, duplicate validation
    # -------------------------------------------------------------------
    def test_skill_creation_with_and_without_category(self):
        self.client.force_authenticate(user=self.superadmin_user)
        cat = JobCategory.objects.create(name='Healthcare', description='Medical and caregiving')

        # Skill with category
        res1 = self.client.post('/accounts/admin/skills/', {
            'name': 'Nursing',
            'category': cat.id,
            'is_active': True
        }, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res1.data['category_name'], 'Healthcare')

        # Skill without category (uncategorized)
        res2 = self.client.post('/accounts/admin/skills/', {
            'name': 'Communication',
            'category': None,
            'is_active': True
        }, format='json')
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(res2.data['category'])

    def test_skill_duplicate_validation(self):
        self.client.force_authenticate(user=self.superadmin_user)
        Skill.objects.create(name='Python')

        # Case and whitespace invariant duplicate
        res = self.client.post('/accounts/admin/skills/', {
            'name': '  python  ',
            'is_active': True
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', res.data)

    # -------------------------------------------------------------------
    # 4. Deactivation and safe delete policies for referenced records
    # -------------------------------------------------------------------
    def test_referenced_skill_cannot_be_deleted(self):
        self.client.force_authenticate(user=self.superadmin_user)
        skill = Skill.objects.create(name='React.js')
        
        # Get or create candidate profile
        candidate, _ = CandidateProfile.objects.get_or_create(user=self.candidate_user, defaults={'full_name': 'Test Candidate'})

        # Create CandidateSkill link
        CandidateSkill.objects.create(candidate=candidate, skill=skill, proficiency_level='INTERMEDIATE')

        # Delete attempt must be rejected safely with 400
        res = self.client.delete(f'/accounts/admin/skills/{skill.id}/')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Skill.objects.filter(id=skill.id).exists())

        # Deactivation must succeed
        res_status = self.client.patch(f'/accounts/admin/skills/{skill.id}/status/', {
            'is_active': False
        }, format='json')
        self.assertEqual(res_status.status_code, status.HTTP_200_OK)
        skill.refresh_from_db()
        self.assertFalse(skill.is_active)
        # Relationship remains intact!
        self.assertEqual(candidate.candidate_skills.count(), 1)

    # -------------------------------------------------------------------
    # 5. Public active catalog endpoints
    # -------------------------------------------------------------------
    def test_public_catalog_endpoints(self):
        cat_active = JobCategory.objects.create(name='Retail', description='Store management', is_active=True)
        cat_inactive = JobCategory.objects.create(name='Discontinued', description='Old category', is_active=False)

        skill_active = Skill.objects.create(name='Cashiering', category=cat_active, is_active=True)
        skill_inactive = Skill.objects.create(name='Obsolete Tech', is_active=False)

        # Anonymous request to public categories endpoint
        res_cat = self.client.get('/accounts/job-categories/')
        self.assertEqual(res_cat.status_code, status.HTTP_200_OK)
        cat_names = [c['name'] for c in res_cat.data]
        self.assertIn('Retail', cat_names)
        self.assertNotIn('Discontinued', cat_names)

        # Anonymous request to public skills endpoint
        res_skills = self.client.get('/accounts/skills/')
        self.assertEqual(res_skills.status_code, status.HTTP_200_OK)
        skill_names = [s['name'] for s in res_skills.data]
        self.assertIn('Cashiering', skill_names)
        self.assertNotIn('Obsolete Tech', skill_names)

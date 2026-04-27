
THREE.OrbitControls = function(camera, domElement) {
    this.camera = camera;
    this.domElement = domElement;
    this.target = new THREE.Vector3();
    this.enableDamping = true;
    this.dampingFactor = 0.08;
    this.rotateSpeed = 0.5;
    this.zoomSpeed = 1.0;
    this.panSpeed = 0.8;
    this.minDistance = 20;
    this.maxDistance = 200;
    this.minPolarAngle = 0.2;
    this.maxPolarAngle = Math.PI / 2.2;
    this.enableKeys = false;
    var scope = this;
    var STATE = { NONE: -1, ROTATE: 0, ZOOM: 1, PAN: 2 };
    var state = STATE.NONE;
    var spherical = new THREE.Spherical();
    var sphericalDelta = new THREE.Spherical();
    var panOffset = new THREE.Vector3();
    var scale = 1;
    var rotateStart = new THREE.Vector2();
    var rotateEnd = new THREE.Vector2();
    var panStart = new THREE.Vector2();
    var panEnd = new THREE.Vector2();
    function getAutoRotationAngle() { return 0; }
    function getZoomScale() { return Math.pow(0.95, scope.zoomSpeed); }
    function rotateLeft(angle) { sphericalDelta.theta -= angle; }
    function rotateUp(angle) { sphericalDelta.phi -= angle; }
    function panLeft(distance, objectMatrix) {
        var v = new THREE.Vector3();
        v.setFromMatrixColumn(objectMatrix, 0);
        v.multiplyScalar(-distance);
        panOffset.add(v);
    }
    function panUp(distance, objectMatrix) {
        var v = new THREE.Vector3();
        v.setFromMatrixColumn(objectMatrix, 1);
        v.multiplyScalar(distance);
        panOffset.add(v);
    }
    function pan(deltaX, deltaY) {
        var element = scope.domElement;
        var offset = new THREE.Vector3();
        var position = scope.camera.position;
        offset.copy(position).sub(scope.target);
        var targetDistance = offset.length();
        targetDistance *= Math.tan((scope.camera.fov / 2) * Math.PI / 180.0);
        panLeft(2 * deltaX * targetDistance / element.clientHeight * scope.panSpeed, scope.camera.matrix);
        panUp(2 * deltaY * targetDistance / element.clientHeight * scope.panSpeed, scope.camera.matrix);
    }
    this.update = function() {
        var offset = new THREE.Vector3();
        var quat = new THREE.Quaternion().setFromUnitVectors(camera.up, new THREE.Vector3(0, 1, 0));
        var quatInverse = quat.clone().invert();
        var lastPosition = new THREE.Vector3();
        var lastQuaternion = new THREE.Quaternion();
        return function update() {
            var position = scope.camera.position;
            offset.copy(position).sub(scope.target);
            offset.applyQuaternion(quat);
            spherical.setFromVector3(offset);
            spherical.theta += sphericalDelta.theta;
            spherical.phi += sphericalDelta.phi;
            spherical.phi = Math.max(scope.minPolarAngle, Math.min(scope.maxPolarAngle, spherical.phi));
            spherical.makeSafe();
            spherical.radius *= scale;
            spherical.radius = Math.max(scope.minDistance, Math.min(scope.maxDistance, spherical.radius));
            scope.target.add(panOffset);
            offset.setFromSpherical(spherical);
            offset.applyQuaternion(quatInverse);
            position.copy(scope.target).add(offset);
            scope.camera.lookAt(scope.target);
            if (scope.enableDamping) {
                sphericalDelta.theta *= (1 - scope.dampingFactor);
                sphericalDelta.phi *= (1 - scope.dampingFactor);
            } else {
                sphericalDelta.set(0, 0, 0);
            }
            scale = 1;
            panOffset.set(0, 0, 0);
        };
    }();
    function onMouseDown(event) {
        event.preventDefault();
        if (event.button === 0) {
            if (event.shiftKey) { state = STATE.PAN; panStart.set(event.clientX, event.clientY); }
            else { state = STATE.ROTATE; rotateStart.set(event.clientX, event.clientY); }
        } else if (event.button === 1) { state = STATE.ZOOM; }
        else if (event.button === 2) { state = STATE.PAN; panStart.set(event.clientX, event.clientY); }
    }
    function onMouseMove(event) {
        if (state === STATE.ROTATE) {
            rotateEnd.set(event.clientX, event.clientY);
            var d = new THREE.Vector2().subVectors(rotateEnd, rotateStart);
            rotateLeft(2 * Math.PI * d.x / domElement.clientHeight * scope.rotateSpeed);
            rotateUp(2 * Math.PI * d.y / domElement.clientHeight * scope.rotateSpeed);
            rotateStart.copy(rotateEnd);
        } else if (state === STATE.PAN) {
            panEnd.set(event.clientX, event.clientY);
            var d = new THREE.Vector2().subVectors(panEnd, panStart);
            pan(d.x, d.y);
            panStart.copy(panEnd);
        }
    }
    function onMouseUp() { state = STATE.NONE; }
    function onWheel(event) {
        event.preventDefault();
        if (event.deltaY > 0) scale /= getZoomScale();
        else scale *= getZoomScale();
    }
    function onContextMenu(event) { event.preventDefault(); }
    domElement.addEventListener('mousedown', onMouseDown, false);
    domElement.addEventListener('mousemove', onMouseMove, false);
    domElement.addEventListener('mouseup', onMouseUp, false);
    domElement.addEventListener('wheel', onWheel, { passive: false });
    domElement.addEventListener('contextmenu', onContextMenu, false);
    var touchStart = new THREE.Vector2();
    var touchStartDist = 0;
    domElement.addEventListener('touchstart', function(e) {
        if (e.touches.length === 1) { state = STATE.ROTATE; rotateStart.set(e.touches[0].clientX, e.touches[0].clientY); }
        else if (e.touches.length === 2) {
            state = STATE.ZOOM;
            var dx = e.touches[0].clientX - e.touches[1].clientX;
            var dy = e.touches[0].clientY - e.touches[1].clientY;
            touchStartDist = Math.sqrt(dx*dx+dy*dy);
        }
    }, false);
    domElement.addEventListener('touchmove', function(e) {
        e.preventDefault();
        if (state === STATE.ROTATE && e.touches.length === 1) {
            rotateEnd.set(e.touches[0].clientX, e.touches[0].clientY);
            var d = new THREE.Vector2().subVectors(rotateEnd, rotateStart);
            rotateLeft(2 * Math.PI * d.x / domElement.clientHeight * scope.rotateSpeed);
            rotateUp(2 * Math.PI * d.y / domElement.clientHeight * scope.rotateSpeed);
            rotateStart.copy(rotateEnd);
        } else if (state === STATE.ZOOM && e.touches.length === 2) {
            var dx = e.touches[0].clientX - e.touches[1].clientX;
            var dy = e.touches[0].clientY - e.touches[1].clientY;
            var dist = Math.sqrt(dx*dx+dy*dy);
            if (dist > touchStartDist) scale *= getZoomScale();
            else scale /= getZoomScale();
            touchStartDist = dist;
        }
    }, { passive: false });
    domElement.addEventListener('touchend', function() { state = STATE.NONE; }, false);
    this.update();
};
const CATEGORIAS = {
    omega: { cor: '#d69e2e', nome: 'Omega', bg: 'rgba(214,158,46,0.15)' },
    visionario: { cor: '#8b5cf6', nome: 'Visionario', bg: 'rgba(139,92,246,0.15)' },
    estrategista: { cor: '#3b82f6', nome: 'Estrategista', bg: 'rgba(59,130,246,0.15)' },
    politico: { cor: '#ef4444', nome: 'Politico', bg: 'rgba(239,68,68,0.15)' },
    filosofo: { cor: '#06b6d4', nome: 'Filosofo', bg: 'rgba(6,182,212,0.15)' },
    psicologo: { cor: '#ec4899', nome: 'Psicologo', bg: 'rgba(236,72,153,0.15)' },
    jurista: { cor: '#f97316', nome: 'Jurista', bg: 'rgba(249,115,22,0.15)' },
    lado_negro: { cor: '#6b21a8', nome: 'Lado Negro', bg: 'rgba(107,33,168,0.15)' },
    ficticio: { cor: '#14b8a6', nome: 'Ficticio', bg: 'rgba(20,184,166,0.15)' },
    comunicador: { cor: '#eab308', nome: 'Comunicador', bg: 'rgba(234,179,8,0.15)' },
    cientista: { cor: '#22d3ee', nome: 'Cientista', bg: 'rgba(34,211,238,0.15)' },
    militar: { cor: '#65a30d', nome: 'Militar', bg: 'rgba(101,163,13,0.15)' }
};
const LOCAIS = [
    { id: 'agora', nome: 'Agora Central', tipo: 'Espaco Publico', desc: 'Anfiteatro circular para debates coletivos e deliberacoes estrategicas.', pos: [0, 0, 0], cor: '#d69e2e', icone: '🏛', cap: 40, grupo: 'publico' },
    { id: 'torre_estrategia', nome: 'Torre de Estrategia', tipo: 'Escritorio', desc: 'Torre de vidro com 5 andares. Centro de planejamento estrategico.', pos: [-30, 0, -25], cor: '#3b82f6', icone: '🏢', cap: 20, grupo: 'trabalho' },
    { id: 'biblioteca', nome: 'Biblioteca Infinita', tipo: 'Pesquisa', desc: 'Edificio com colunas classicas e acervo ilimitado.', pos: [30, 0, -25], cor: '#92400e', icone: '📚', cap: 25, grupo: 'trabalho' },
    { id: 'cafe', nome: 'Cafe dos Filosofos', tipo: 'Lazer', desc: 'Cafe com terraco. Conversas informais.', pos: [0, 0, -20], cor: '#78350f', icone: '☕', cap: 15, grupo: 'lazer' },
    { id: 'arena', nome: 'Arena de Debates', tipo: 'Espaco Publico', desc: 'Semicirculo para debates e simulacoes.', pos: [-25, 0, 25], cor: '#ef4444', icone: '🎭', cap: 30, grupo: 'publico' },
    { id: 'jardim', nome: 'Jardim dos Visionarios', tipo: 'Lazer', desc: 'Jardim aberto. Contemplacao e brainstorming.', pos: [35, 0, 0], cor: '#22c55e', icone: '🌳', cap: 20, grupo: 'lazer' },
    { id: 'tribunal', nome: 'Tribunal da Razao', tipo: 'Especial', desc: 'Edificio classico com colunas de marmore. Onde se julga a logica dos argumentos.', pos: [-15, 0, 30], cor: '#94a3b8', icone: '⚖', cap: 15, grupo: 'especial' },
    { id: 'laboratorio', nome: 'Laboratorio de Ideias', tipo: 'Pesquisa', desc: 'Edificio angular moderno. Incubadora de conceitos radicais e inovacoes.', pos: [0, 0, -35], cor: '#2563eb', icone: '🔬', cap: 20, grupo: 'trabalho' },
    { id: 'galeria', nome: 'Galeria dos Legados', tipo: 'Cultural', desc: 'Museu longo exibindo as contribuicoes de cada consultor para a historia.', pos: [40, 0, -10], cor: '#fafaf9', icone: '🏛', cap: 18, grupo: 'lazer' },
    { id: 'sala_guerra', nome: 'Sala de Guerra', tipo: 'Operacional', desc: 'Bunker discreto para operacoes taticas e analise de cenarios criticos.', pos: [-40, 0, 0], cor: '#374151', icone: '🎯', cap: 12, grupo: 'trabalho' },
    { id: 'auditorio', nome: 'Auditorio INTEIA', tipo: 'Eventos', desc: 'Grande domo com acabamento dourado para apresentacoes e keynotes.', pos: [-20, 0, 5], cor: '#b7791f', icone: '🎪', cap: 50, grupo: 'publico' },
    { id: 'atelie', nome: 'Atelie dos Artesaos', tipo: 'Criativo', desc: 'Estudio colorido para trabalhos criativos, design thinking e prototipacao.', pos: [35, 0, 20], cor: '#db2777', icone: '🎨', cap: 15, grupo: 'trabalho' },
    { id: 'observatorio', nome: 'Observatorio do Futuro', tipo: 'Pesquisa', desc: 'Torre fina com domo prateado. Analise de tendencias e prospeccao.', pos: [35, 0, -35], cor: '#c0c0c0', icone: '🔭', cap: 10, grupo: 'especial' },
    { id: 'res_norte', nome: 'Residencias Norte', tipo: 'Residencial', desc: 'Bloco moderno de apartamentos com vista para os laboratorios.', pos: [0, 0, -50], cor: '#64748b', icone: '🏠', cap: 35, grupo: 'residencia' },
    { id: 'res_sul', nome: 'Residencias Sul', tipo: 'Residencial', desc: 'Apartamentos classicos com jardins privativos e area de convivencia.', pos: [0, 0, 50], cor: '#a16207', icone: '🏡', cap: 35, grupo: 'residencia' },
    { id: 'res_leste', nome: 'Residencias Leste', tipo: 'Residencial', desc: 'Apartamentos zen com jardim japones e espaco de meditacao.', pos: [50, 0, 0], cor: '#15803d', icone: '🏘', cap: 35, grupo: 'residencia' },
    { id: 'res_oeste', nome: 'Residencias Oeste', tipo: 'Residencial', desc: 'Apartamentos executivos com escritorio privado integrado.', pos: [-50, 0, 0], cor: '#1e293b', icone: '🏢', cap: 35, grupo: 'residencia' },
    { id: 'refeitorio', nome: 'Refeitorio Central', tipo: 'Alimentacao', desc: 'Amplo espaco de refeicoes com culinaria internacional. Ponto de encontro.', pos: [-5, 0, 15], cor: '#ea580c', icone: '🍽', cap: 40, grupo: 'lazer' },
    { id: 'terraco', nome: 'Terraco Panoramico', tipo: 'Mirante', desc: 'Plataforma elevada com vista 360 graus do campus. Ideal para networking.', pos: [15, 0, 10], cor: '#0ea5e9', icone: '🌅', cap: 20, grupo: 'lazer' }
];
const AGENTES = [
    { id:'IGOR001', nome:'Igor Morais', cat:'omega', tier:'S', titulo:'Presidente INTEIA' },
    { id:'CL085', nome:'Helena Montenegro', cat:'omega', tier:'S', titulo:'Agente IA Avancada' },
    { id:'CL001', nome:'Elon Musk', cat:'visionario', tier:'S', titulo:'Inovador Disruptivo' },
    { id:'CL002', nome:'Steve Jobs', cat:'visionario', tier:'S', titulo:'Design Thinking' },
    { id:'CL003', nome:'Jeff Bezos', cat:'visionario', tier:'A', titulo:'Escala e Logistica' },
    { id:'CL004', nome:'Sun Tzu', cat:'estrategista', tier:'S', titulo:'Estrategista Militar' },
    { id:'CL005', nome:'Warren Buffett', cat:'estrategista', tier:'S', titulo:'Oraculo Financeiro' },
    { id:'CL006', nome:'Maquiavel', cat:'lado_negro', tier:'S', titulo:'Poder e Pragmatismo' },
    { id:'CL007', nome:'Bernie Madoff', cat:'lado_negro', tier:'A', titulo:'Engenharia de Fraude' },
    { id:'CL008', nome:'Elizabeth Holmes', cat:'lado_negro', tier:'A', titulo:'Manipulacao Narrativa' },
    { id:'CL009', nome:'Frank Abagnale', cat:'lado_negro', tier:'B', titulo:'Engenharia Social' },
    { id:'CL010', nome:'Rui Barbosa', cat:'jurista', tier:'S', titulo:'Jurista Supremo' },
    { id:'CL011', nome:'Ruth Bader Ginsburg', cat:'jurista', tier:'S', titulo:'Justica e Igualdade' },
    { id:'CL012', nome:'Socrates', cat:'filosofo', tier:'S', titulo:'Metodo Socratico' },
    { id:'CL013', nome:'Aristoteles', cat:'filosofo', tier:'S', titulo:'Logica Formal' },
    { id:'CL014', nome:'Nietzsche', cat:'filosofo', tier:'A', titulo:'Vontade de Poder' },
    { id:'CL015', nome:'Simone de Beauvoir', cat:'filosofo', tier:'A', titulo:'Existencialismo' },
    { id:'CL016', nome:'Carl Jung', cat:'psicologo', tier:'S', titulo:'Inconsciente Coletivo' },
    { id:'CL017', nome:'Sigmund Freud', cat:'psicologo', tier:'S', titulo:'Psicanalise' },
    { id:'CL018', nome:'Daniel Kahneman', cat:'psicologo', tier:'S', titulo:'Vieses Cognitivos' },
    { id:'CL019', nome:'Lula', cat:'politico', tier:'S', titulo:'Articulacao Popular' },
    { id:'CL020', nome:'Winston Churchill', cat:'politico', tier:'S', titulo:'Lideranca na Crise' },
    { id:'CL021', nome:'Angela Merkel', cat:'politico', tier:'S', titulo:'Pragmatismo Europeu' },
    { id:'CL022', nome:'Juscelino Kubitschek', cat:'politico', tier:'A', titulo:'Desenvolvimentismo' },
    { id:'CL023', nome:'Don Corleone', cat:'ficticio', tier:'S', titulo:'Ofertas Irrecusaveis' },
    { id:'CL024', nome:'Sherlock Holmes', cat:'ficticio', tier:'S', titulo:'Deducao Logica' },
    { id:'CL025', nome:'Tony Stark', cat:'ficticio', tier:'S', titulo:'Engenharia Genial' },
    { id:'CL026', nome:'Walter White', cat:'ficticio', tier:'A', titulo:'Quimica do Poder' },
    { id:'CL027', nome:'Gandalf', cat:'ficticio', tier:'A', titulo:'Sabedoria Milenar' },
    { id:'CL028', nome:'Tyrion Lannister', cat:'ficticio', tier:'A', titulo:'Intriga Politica' },
    { id:'CL029', nome:'Oprah Winfrey', cat:'comunicador', tier:'S', titulo:'Influencia de Massa' },
    { id:'CL030', nome:'Carl Sagan', cat:'cientista', tier:'S', titulo:'Divulgacao Cientifica' },
    { id:'CL031', nome:'Marie Curie', cat:'cientista', tier:'S', titulo:'Pesquisa Pioneira' },
    { id:'CL032', nome:'Napoleao Bonaparte', cat:'militar', tier:'S', titulo:'Genio Tatico' },
    { id:'CL033', nome:'Clausewitz', cat:'militar', tier:'S', titulo:'Teoria da Guerra' },
    { id:'CL034', nome:'Ada Lovelace', cat:'cientista', tier:'A', titulo:'Computacao Pioneira' },
    { id:'CL035', nome:'Alan Turing', cat:'cientista', tier:'S', titulo:'Inteligencia Artificial' },
    { id:'CL036', nome:'Confucio', cat:'filosofo', tier:'S', titulo:'Etica e Harmonia' },
    { id:'CL037', nome:'Marcus Aurelius', cat:'filosofo', tier:'A', titulo:'Estoicismo' },
    { id:'CL038', nome:'Cleopatra', cat:'politico', tier:'A', titulo:'Diplomacia Sedutora' },
    { id:'CL039', nome:'Mahatma Gandhi', cat:'politico', tier:'S', titulo:'Resistencia Pacifica' },
    { id:'CL040', nome:'Nelson Mandela', cat:'politico', tier:'S', titulo:'Reconciliacao' },
    { id:'CL041', nome:'Nikola Tesla', cat:'cientista', tier:'S', titulo:'Invencao Radical' },
    { id:'CL042', nome:'Leonardo da Vinci', cat:'visionario', tier:'S', titulo:'Polimata Universal' },
    { id:'CL043', nome:'Peter Drucker', cat:'estrategista', tier:'S', titulo:'Gestao Moderna' },
    { id:'CL044', nome:'Philip Kotler', cat:'estrategista', tier:'A', titulo:'Marketing Estrategico' },
    { id:'CL045', nome:'Darth Vader', cat:'ficticio', tier:'A', titulo:'Lado Sombrio' },
    { id:'CL046', nome:'Hannibal Lecter', cat:'lado_negro', tier:'S', titulo:'Perfilagem Criminal' },
    { id:'CL047', nome:'Jordan Belfort', cat:'lado_negro', tier:'B', titulo:'Vendas Agressivas' },
    { id:'CL048', nome:'Miyamoto Musashi', cat:'estrategista', tier:'S', titulo:'Disciplina Marcial' }
];
AGENTES.forEach(a => {
    a.local = LOCAIS[Math.floor(Math.random() * LOCAIS.length)].id;
    a.targetLocal = a.local;
    a.progress = 1;
    a.moving = false;
});
AGENTES[0].local = 'agora';
AGENTES[1].local = 'torre_estrategia';
const canvas = document.getElementById('canvas3d');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x87ceeb);
scene.fog = new THREE.Fog(0x87ceeb, 120, 250);
const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.5, 500);
camera.position.set(70, 65, 70);
const controls = new THREE.OrbitControls(camera, canvas);
controls.target.set(0, 0, 0);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.minDistance = 20;
controls.maxDistance = 180;
controls.update();
const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
scene.add(ambientLight);
const sunLight = new THREE.DirectionalLight(0xfff5e6, 1.0);
sunLight.position.set(50, 80, 30);
sunLight.castShadow = true;
sunLight.shadow.mapSize.width = 2048;
sunLight.shadow.mapSize.height = 2048;
sunLight.shadow.camera.near = 1;
sunLight.shadow.camera.far = 200;
sunLight.shadow.camera.left = -80;
sunLight.shadow.camera.right = 80;
sunLight.shadow.camera.top = 80;
sunLight.shadow.camera.bottom = -80;
scene.add(sunLight);
const hemisphereLight = new THREE.HemisphereLight(0x87ceeb, 0x3a7d0a, 0.3);
scene.add(hemisphereLight);
const groundGeo = new THREE.PlaneGeometry(200, 200);
const groundMat = new THREE.MeshPhongMaterial({ color: 0x4a8c3f, shininess: 5 });
const ground = new THREE.Mesh(groundGeo, groundMat);
ground.rotation.x = -Math.PI / 2;
ground.position.y = -0.1;
ground.receiveShadow = true;
scene.add(ground);
const subGroundGeo = new THREE.PlaneGeometry(220, 220);
const subGroundMat = new THREE.MeshPhongMaterial({ color: 0x2d5a27 });
const subGround = new THREE.Mesh(subGroundGeo, subGroundMat);
subGround.rotation.x = -Math.PI / 2;
subGround.position.y = -0.2;
scene.add(subGround);
const buildingGroups = {};
const buildingMeshes = [];
const labelSprites = [];
function makeColor(hex) { return new THREE.Color(hex); }
function makeMat(color, opts = {}) {
    return new THREE.MeshPhongMaterial({
        color: new THREE.Color(color),
        shininess: opts.shininess || 30,
        transparent: opts.transparent || false,
        opacity: opts.opacity || 1,
        emissive: opts.emissive ? new THREE.Color(opts.emissive) : new THREE.Color(0x000000),
        emissiveIntensity: opts.emissiveIntensity || 0
    });
}
function addWindows(parent, w, h, d, color) {
    const winMat = makeMat('#1e293b', { emissive: '#fbbf24', emissiveIntensity: 0.3 });
    const winGeo = new THREE.BoxGeometry(0.4, 0.5, 0.05);
    for (let y = 0.8; y < h - 0.3; y += 1.2) {
        for (let x = -w/2 + 0.8; x < w/2 - 0.4; x += 1.2) {
            const wf = new THREE.Mesh(winGeo, winMat);
            wf.position.set(x, y, d/2 + 0.02);
            parent.add(wf);
            const wb = new THREE.Mesh(winGeo, winMat);
            wb.position.set(x, y, -d/2 - 0.02);
            parent.add(wb);
        }
        for (let z = -d/2 + 0.8; z < d/2 - 0.4; z += 1.2) {
            const wl = new THREE.Mesh(winGeo.clone(), winMat);
            wl.rotation.y = Math.PI / 2;
            wl.position.set(w/2 + 0.02, y, z);
            parent.add(wl);
            const wr = new THREE.Mesh(winGeo.clone(), winMat);
            wr.rotation.y = Math.PI / 2;
            wr.position.set(-w/2 - 0.02, y, z);
            parent.add(wr);
        }
    }
}
function makeLabel(text, y) {
    const c = document.createElement('canvas');
    c.width = 512; c.height = 64;
    const ctx = c.getContext('2d');
    ctx.fillStyle = 'rgba(15,23,42,0.85)';
    ctx.roundRect(0, 8, 512, 48, 12);
    ctx.fill();
    ctx.strokeStyle = 'rgba(214,158,46,0.6)';
    ctx.lineWidth = 2;
    ctx.roundRect(0, 8, 512, 48, 12);
    ctx.stroke();
    ctx.fillStyle = '#f8fafc';
    ctx.font = 'bold 26px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, 256, 32);
    const tex = new THREE.CanvasTexture(c);
    const mat = new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false });
    const sprite = new THREE.Sprite(mat);
    sprite.scale.set(8, 1, 1);
    sprite.position.y = y;
    sprite.renderOrder = 1;
    return sprite;
}
function makeTree(x, z, scale) {
    const g = new THREE.Group();
    const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.15 * scale, 0.2 * scale, 1.5 * scale, 6), makeMat('#5c3317'));
    trunk.position.set(x, 0.75 * scale, z);
    trunk.castShadow = true;
    g.add(trunk);
    const foliage = new THREE.Mesh(new THREE.ConeGeometry(1.2 * scale, 2.5 * scale, 7), makeMat('#2d7d2d'));
    foliage.position.set(x, 2.5 * scale, z);
    foliage.castShadow = true;
    g.add(foliage);
    const foliage2 = new THREE.Mesh(new THREE.ConeGeometry(0.9 * scale, 2 * scale, 7), makeMat('#3a9e3a'));
    foliage2.position.set(x, 3.2 * scale, z);
    foliage2.castShadow = true;
    g.add(foliage2);
    return g;
}
function makeBush(x, z, s) {
    const g = new THREE.Group();
    const m = makeMat('#2d7d2d');
    const b1 = new THREE.Mesh(new THREE.SphereGeometry(0.5*s, 6, 5), m);
    b1.position.set(x, 0.3*s, z);
    b1.scale.y = 0.7;
    g.add(b1);
    const b2 = new THREE.Mesh(new THREE.SphereGeometry(0.35*s, 6, 5), makeMat('#3a9e3a'));
    b2.position.set(x + 0.3*s, 0.4*s, z + 0.2*s);
    b2.scale.y = 0.7;
    g.add(b2);
    return g;
}
function buildAgora(loc) {
    const g = new THREE.Group();
    const ringGeo = new THREE.TorusGeometry(5, 0.6, 8, 32);
    const ringMat = makeMat('#d69e2e', { shininess: 80 });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = -Math.PI / 2;
    ring.position.y = 0.5;
    ring.castShadow = true;
    g.add(ring);
    const floor = new THREE.Mesh(new THREE.CylinderGeometry(5, 5, 0.3, 32), makeMat('#f5f0e1'));
    floor.position.y = 0.15;
    floor.receiveShadow = true;
    g.add(floor);
    for (let i = 0; i < 3; i++) {
        const step = new THREE.Mesh(new THREE.CylinderGeometry(6 + i, 6 + i, 0.2, 32), makeMat('#d4c8a8'));
        step.position.y = -0.1 * i;
        step.receiveShadow = true;
        g.add(step);
    }
    for (let i = 0; i < 8; i++) {
        const angle = (i / 8) * Math.PI * 2;
        const col = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.25, 3, 8), makeMat('#e8dcc8'));
        col.position.set(Math.cos(angle) * 5.5, 1.5, Math.sin(angle) * 5.5);
        col.castShadow = true;
        g.add(col);
    }
    const fountain = new THREE.Mesh(new THREE.CylinderGeometry(1.2, 1.5, 0.8, 16), makeMat('#94a3b8'));
    fountain.position.y = 0.7;
    g.add(fountain);
    const water = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 0.1, 16), makeMat('#3b82f6', { transparent: true, opacity: 0.7 }));
    water.position.y = 1.1;
    g.add(water);
    g.add(makeLabel(loc.nome, 5));
    return g;
}
function buildTower(loc, color, floors, width) {
    const g = new THREE.Group();
    const h = floors * 2.5;
    const body = new THREE.Mesh(new THREE.BoxGeometry(width, h, width * 0.8), makeMat(color, { shininess: 60 }));
    body.position.y = h / 2;
    body.castShadow = true;
    body.receiveShadow = true;
    g.add(body);
    addWindows(g, width, h, width * 0.8, color);
    const roof = new THREE.Mesh(new THREE.BoxGeometry(width + 0.4, 0.3, width * 0.8 + 0.4), makeMat('#d69e2e'));
    roof.position.y = h + 0.15;
    g.add(roof);
    const ant = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 2, 4), makeMat('#94a3b8'));
    ant.position.y = h + 1.15;
    g.add(ant);
    g.add(makeLabel(loc.nome, h + 3));
    return g;
}
function buildClassic(loc, color, w, d, h) {
    const g = new THREE.Group();
    const body = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), makeMat(color));
    body.position.y = h / 2;
    body.castShadow = true;
    body.receiveShadow = true;
    g.add(body);
    addWindows(g, w, h, d, color);
    const numCols = Math.floor(w / 2);
    for (let i = 0; i < numCols; i++) {
        const x = -w/2 + 1 + i * (w - 2) / (numCols - 1);
        const col = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.2, h + 0.5, 8), makeMat('#e8dcc8'));
        col.position.set(x, h / 2, d / 2 + 0.3);
        col.castShadow = true;
        g.add(col);
    }
    const pedGeo = new THREE.BufferGeometry();
    const verts = new Float32Array([ -w/2 - 0.2, h, d/2 + 0.5,  w/2 + 0.2, h, d/2 + 0.5,  0, h + 1.5, d/2 + 0.5 ]);
    pedGeo.setAttribute('position', new THREE.BufferAttribute(verts, 3));
    pedGeo.computeVertexNormals();
    const ped = new THREE.Mesh(pedGeo, makeMat('#d4c8a8'));
    g.add(ped);
    const stepMat = makeMat('#d4c8a8');
    for (let i = 0; i < 3; i++) {
        const step = new THREE.Mesh(new THREE.BoxGeometry(w + 1 + i * 0.5, 0.15, 0.5), stepMat);
        step.position.set(0, 0.07 - i * 0.15, d / 2 + 0.5 + i * 0.5);
        g.add(step);
    }
    g.add(makeLabel(loc.nome, h + 3));
    return g;
}
function buildModern(loc, color, w, d, h) {
    const g = new THREE.Group();
    const body = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), makeMat(color, { shininess: 50 }));
    body.position.y = h / 2;
    body.castShadow = true;
    g.add(body);
    addWindows(g, w, h, d, color);
    const accent = new THREE.Mesh(new THREE.BoxGeometry(w * 0.3, h + 0.5, d + 0.4), makeMat(color, { emissive: color, emissiveIntensity: 0.1 }));
    accent.position.set(-w * 0.35, h / 2, 0);
    accent.castShadow = true;
    g.add(accent);
    const roofEdge = new THREE.Mesh(new THREE.BoxGeometry(w + 0.3, 0.15, d + 0.3), makeMat('#1e293b'));
    roofEdge.position.y = h + 0.07;
    g.add(roofEdge);
    g.add(makeLabel(loc.nome, h + 2.5));
    return g;
}
function buildDome(loc, color, radius, h) {
    const g = new THREE.Group();
    const base = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, h, 24), makeMat(color));
    base.position.y = h / 2;
    base.castShadow = true;
    g.add(base);
    const dome = new THREE.Mesh(new THREE.SphereGeometry(radius * 0.9, 24, 16, 0, Math.PI * 2, 0, Math.PI / 2), makeMat('#d69e2e', { shininess: 80 }));
    dome.position.y = h;
    dome.castShadow = true;
    g.add(dome);
    const door = new THREE.Mesh(new THREE.BoxGeometry(1.5, 2.5, 0.1), makeMat('#3a2010'));
    door.position.set(0, 1.25, radius + 0.05);
    g.add(door);
    const winMat = makeMat('#1e293b', { emissive: '#fbbf24', emissiveIntensity: 0.3 });
    for (let i = 0; i < 12; i++) {
        const angle = (i / 12) * Math.PI * 2;
        const win = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.8, 0.05), winMat);
        win.position.set(Math.cos(angle) * (radius + 0.02), h * 0.6, Math.sin(angle) * (radius + 0.02));
        win.lookAt(new THREE.Vector3(0, h * 0.6, 0));
        g.add(win);
    }
    g.add(makeLabel(loc.nome, h + radius + 2));
    return g;
}
function buildObservatory(loc) {
    const g = new THREE.Group();
    const tower = new THREE.Mesh(new THREE.CylinderGeometry(1, 1.3, 10, 12), makeMat('#94a3b8', { shininess: 60 }));
    tower.position.y = 5;
    tower.castShadow = true;
    g.add(tower);
    const deck = new THREE.Mesh(new THREE.CylinderGeometry(2, 1.5, 1, 12), makeMat('#64748b'));
    deck.position.y = 10.5;
    g.add(deck);
    const dome = new THREE.Mesh(new THREE.SphereGeometry(2, 16, 12, 0, Math.PI * 2, 0, Math.PI / 2), makeMat('#c0c0c0', { shininess: 90 }));
    dome.position.y = 11;
    g.add(dome);
    const winBand = new THREE.Mesh(new THREE.TorusGeometry(1.8, 0.15, 4, 24), makeMat('#1e293b', { emissive: '#fbbf24', emissiveIntensity: 0.4 }));
    winBand.rotation.x = Math.PI / 2;
    winBand.position.y = 10.5;
    g.add(winBand);
    g.add(makeLabel(loc.nome, 14));
    return g;
}
function buildGarden(loc) {
    const g = new THREE.Group();
    const gardenBase = new THREE.Mesh(new THREE.CylinderGeometry(6, 6, 0.15, 32), makeMat('#3a7d0a'));
    gardenBase.position.y = 0.07;
    g.add(gardenBase);
    const pathMat = makeMat('#d4c8a8');
    const p1 = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.05, 12), pathMat);
    p1.position.y = 0.17;
    g.add(p1);
    const p2 = new THREE.Mesh(new THREE.BoxGeometry(12, 0.05, 0.5), pathMat);
    p2.position.y = 0.17;
    g.add(p2);
    const treePositions = [[-3,0,-3],[3,0,-3],[-3,0,3],[3,0,3],[0,0,-4.5],[0,0,4.5],[-4.5,0,0],[4.5,0,0]];
    treePositions.forEach(p => { g.add(makeTree(p[0], p[2], 0.8 + Math.random() * 0.4)); });
    const benchMat = makeMat('#78350f');
    [[-2, 0, 0], [2, 0, 0]].forEach(p => {
        const bench = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.3, 0.5), benchMat);
        bench.position.set(p[0], 0.4, p[2]);
        g.add(bench);
        const backrest = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.5, 0.1), benchMat);
        backrest.position.set(p[0], 0.65, p[2] - 0.2);
        g.add(backrest);
    });
    for (let i = 0; i < 20; i++) {
        const angle = Math.random() * Math.PI * 2;
        const dist = 1.5 + Math.random() * 3.5;
        const flower = new THREE.Mesh(
            new THREE.SphereGeometry(0.15, 5, 5),
            makeMat(['#ef4444','#ec4899','#f59e0b','#8b5cf6','#f43f5e'][Math.floor(Math.random()*5)])
        );
        flower.position.set(Math.cos(angle)*dist, 0.2, Math.sin(angle)*dist);
        g.add(flower);
    }
    g.add(makeLabel(loc.nome, 5));
    return g;
}
function buildSemiCircle(loc, color) {
    const g = new THREE.Group();
    for (let t = 0; t < 4; t++) {
        const r = 4 + t * 1.2;
        const geo = new THREE.CylinderGeometry(r, r, 0.6, 24, 1, false, 0, Math.PI);
        const tier = new THREE.Mesh(geo, makeMat(t === 0 ? color : '#64748b'));
        tier.position.y = 0.3 + t * 0.6;
        tier.castShadow = true;
        g.add(tier);
    }
    const stage = new THREE.Mesh(new THREE.BoxGeometry(5, 0.4, 3), makeMat('#1e293b'));
    stage.position.set(0, 0.2, -3);
    stage.receiveShadow = true;
    g.add(stage);
    const strip = new THREE.Mesh(new THREE.BoxGeometry(5.2, 0.1, 0.2), makeMat(color, { emissive: color, emissiveIntensity: 0.5 }));
    strip.position.set(0, 0.42, -3);
    g.add(strip);
    g.add(makeLabel(loc.nome, 5));
    return g;
}
function buildBunker(loc, color) {
    const g = new THREE.Group();
    const body = new THREE.Mesh(new THREE.BoxGeometry(6, 2, 5), makeMat(color));
    body.position.y = 1;
    body.castShadow = true;
    g.add(body);
    const roof = new THREE.Mesh(new THREE.BoxGeometry(6.5, 0.5, 5.5), makeMat('#1e293b'));
    roof.position.y = 2.25;
    g.add(roof);
    const winMat = makeMat('#0f172a', { emissive: '#ef4444', emissiveIntensity: 0.3 });
    for (let i = 0; i < 3; i++) {
        const win = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.2, 0.05), winMat);
        win.position.set(-1.5 + i * 1.5, 1.5, 2.53);
        g.add(win);
    }
    for (let i = 0; i < 3; i++) {
        const ant = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 1.5 + i * 0.3, 4), makeMat('#94a3b8'));
        ant.position.set(-1.5 + i * 1.5, 3 + i * 0.15, 0);
        g.add(ant);
    }
    const door = new THREE.Mesh(new THREE.BoxGeometry(1.2, 1.8, 0.1), makeMat('#1e293b'));
    door.position.set(0, 0.9, 2.55);
    g.add(door);
    g.add(makeLabel(loc.nome, 5));
    return g;
}
function buildApartment(loc, color, style) {
    const g = new THREE.Group();
    const w = 8, h = 4, d = 5;
    const body = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), makeMat(color));
    body.position.y = h / 2;
    body.castShadow = true;
    g.add(body);
    addWindows(g, w, h, d, color);
    if (style === 'modern') {
        for (let y = 1.5; y < h; y += 2) {
            for (let x = -2.5; x <= 2.5; x += 2.5) {
                const bal = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.1, 0.8), makeMat('#94a3b8', { transparent: true, opacity: 0.5 }));
                bal.position.set(x, y, d / 2 + 0.4);
                g.add(bal);
            }
        }
    } else if (style === 'classic') {
        const roofGeo = new THREE.BufferGeometry();
        const rv = new Float32Array([
            -w/2-0.2, h, -d/2-0.2,  w/2+0.2, h, -d/2-0.2,  w/2+0.2, h, d/2+0.2,  -w/2-0.2, h, d/2+0.2,
            -w/2-0.2, h, -d/2-0.2,  0, h+1.5, 0,  w/2+0.2, h, -d/2-0.2,
            w/2+0.2, h, -d/2-0.2,  0, h+1.5, 0,  w/2+0.2, h, d/2+0.2,
            w/2+0.2, h, d/2+0.2,  0, h+1.5, 0,  -w/2-0.2, h, d/2+0.2,
            -w/2-0.2, h, d/2+0.2,  0, h+1.5, 0,  -w/2-0.2, h, -d/2-0.2
        ]);
        const ri = [0,1,2, 0,2,3, 4,5,6, 7,8,9, 10,11,12, 13,14,15];
        roofGeo.setAttribute('position', new THREE.BufferAttribute(rv, 3));
        roofGeo.setIndex(ri);
        roofGeo.computeVertexNormals();
        const roofMesh = new THREE.Mesh(roofGeo, makeMat('#8b4513'));
        g.add(roofMesh);
    } else if (style === 'zen') {
        const wall = new THREE.Mesh(new THREE.BoxGeometry(w + 2, 0.6, d + 2), makeMat('#15803d', { transparent: true, opacity: 0.3 }));
        wall.position.y = 0.3;
        g.add(wall);
        g.add(makeTree(w/2 + 1, 0, 0.5));
        g.add(makeTree(-w/2 - 1, 0, 0.5));
    } else { 
        const pilMat = makeMat('#0f172a');
        [[-w/2, d/2], [w/2, d/2], [-w/2, -d/2], [w/2, -d/2]].forEach(([px, pz]) => {
            const pil = new THREE.Mesh(new THREE.BoxGeometry(0.3, h + 0.5, 0.3), pilMat);
            pil.position.set(px, h/2, pz);
            g.add(pil);
        });
    }
    const roofEdge = new THREE.Mesh(new THREE.BoxGeometry(w + 0.3, 0.1, d + 0.3), makeMat('#475569'));
    roofEdge.position.y = h + 0.05;
    g.add(roofEdge);
    g.add(makeLabel(loc.nome, h + 3));
    return g;
}
function buildCafe(loc) {
    const g = new THREE.Group();
    const body = new THREE.Mesh(new THREE.BoxGeometry(4, 3, 3.5), makeMat('#78350f'));
    body.position.y = 1.5;
    body.castShadow = true;
    g.add(body);
    addWindows(g, 4, 3, 3.5, '#78350f');
    const terrace = new THREE.Mesh(new THREE.BoxGeometry(5, 0.15, 4.5), makeMat('#a16207'));
    terrace.position.y = 3.07;
    g.add(terrace);
    const railMat = makeMat('#d4c8a8');
    const railGeo = new THREE.BoxGeometry(0.05, 0.6, 4.5);
    const r1 = new THREE.Mesh(railGeo, railMat); r1.position.set(2.5, 3.4, 0); g.add(r1);
    const r2 = new THREE.Mesh(railGeo, railMat); r2.position.set(-2.5, 3.4, 0); g.add(r2);
    const railGeo2 = new THREE.BoxGeometry(5, 0.6, 0.05);
    const r3 = new THREE.Mesh(railGeo2, railMat); r3.position.set(0, 3.4, 2.25); g.add(r3);
    const r4 = new THREE.Mesh(railGeo2, railMat); r4.position.set(0, 3.4, -2.25); g.add(r4);
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 1.5, 4), makeMat('#5c3317'));
    pole.position.set(1, 4, 1);
    g.add(pole);
    const umbrella = new THREE.Mesh(new THREE.ConeGeometry(1.2, 0.5, 8), makeMat('#ef4444'));
    umbrella.position.set(1, 4.8, 1);
    g.add(umbrella);
    const door = new THREE.Mesh(new THREE.BoxGeometry(0.8, 1.6, 0.1), makeMat('#3a2010'));
    door.position.set(0, 0.8, 1.78);
    g.add(door);
    const awning = new THREE.Mesh(new THREE.BoxGeometry(2, 0.1, 1), makeMat('#b91c1c'));
    awning.position.set(0, 2.2, 2.2);
    awning.rotation.x = -0.15;
    g.add(awning);
    g.add(makeLabel(loc.nome, 6));
    return g;
}
function buildRefeitorio(loc) {
    const g = new THREE.Group();
    const body = new THREE.Mesh(new THREE.BoxGeometry(8, 2.5, 5), makeMat('#ea580c'));
    body.position.y = 1.25;
    body.castShadow = true;
    g.add(body);
    addWindows(g, 8, 2.5, 5, '#ea580c');
    const canopy = new THREE.Mesh(new THREE.BoxGeometry(4, 0.1, 2), makeMat('#d69e2e'));
    canopy.position.set(0, 2.5, 3.5);
    g.add(canopy);
    [[-1.8, 3.5], [1.8, 3.5]].forEach(([x, z]) => {
        const col = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 2.5, 6), makeMat('#e8dcc8'));
        col.position.set(x, 1.25, z);
        g.add(col);
    });
    const stack = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 1.5, 8), makeMat('#6b7280'));
    stack.position.set(3, 3.25, -1);
    g.add(stack);
    g.add(makeLabel(loc.nome, 5));
    return g;
}
function buildTerraco(loc) {
    const g = new THREE.Group();
    const platform = new THREE.Mesh(new THREE.BoxGeometry(7, 2, 6), makeMat('#0ea5e9', { transparent: true, opacity: 0.5 }));
    platform.position.y = 1;
    g.add(platform);
    const top = new THREE.Mesh(new THREE.BoxGeometry(7.2, 0.2, 6.2), makeMat('#0ea5e9'));
    top.position.y = 2.1;
    top.receiveShadow = true;
    g.add(top);
    const railMat = makeMat('#94a3b8');
    const posts = [[-3.4, 0, -2.9],[-3.4, 0, 2.9],[3.4, 0, -2.9],[3.4, 0, 2.9],[-3.4,0,0],[3.4,0,0],[0,0,-2.9],[0,0,2.9]];
    posts.forEach(([x, _, z]) => {
        const post = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 1.2, 4), railMat);
        post.position.set(x, 2.8, z);
        g.add(post);
    });
    [[7.2, 0.04, 0.04, 0, 3.2, -2.9],[7.2, 0.04, 0.04, 0, 3.2, 2.9],[0.04, 0.04, 6.2, -3.4, 3.2, 0],[0.04, 0.04, 6.2, 3.4, 3.2, 0]].forEach(([w,h,d,x,y,z]) => {
        const rail = new THREE.Mesh(new THREE.BoxGeometry(w,h,d), railMat);
        rail.position.set(x,y,z);
        g.add(rail);
    });
    for (let i = 0; i < 5; i++) {
        const step = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.3, 0.6), makeMat('#64748b'));
        step.position.set(-3.8, 0.15 + i * 0.4, -1.5 + i * 0.6);
        g.add(step);
    }
    g.add(makeLabel(loc.nome, 5));
    return g;
}
function buildColorfulStudio(loc) {
    const g = new THREE.Group();
    const body = new THREE.Mesh(new THREE.BoxGeometry(5, 3, 4), makeMat('#f8fafc'));
    body.position.y = 1.5;
    body.castShadow = true;
    g.add(body);
    const colors = ['#ef4444','#3b82f6','#22c55e','#f59e0b','#8b5cf6','#ec4899'];
    for (let i = 0; i < 6; i++) {
        const panel = new THREE.Mesh(new THREE.BoxGeometry(0.7, 2.5, 0.05), makeMat(colors[i]));
        panel.position.set(-2 + i * 0.8, 1.5, 2.03);
        g.add(panel);
    }
    addWindows(g, 5, 3, 4, '#f8fafc');
    const skylight = new THREE.Mesh(new THREE.BoxGeometry(3, 0.1, 2), makeMat('#87ceeb', { transparent: true, opacity: 0.4 }));
    skylight.position.set(0, 3.05, 0);
    skylight.rotation.x = 0.1;
    g.add(skylight);
    g.add(makeLabel(loc.nome, 5));
    return g;
}
function buildMuseum(loc) {
    const g = new THREE.Group();
    const body = new THREE.Mesh(new THREE.BoxGeometry(10, 3, 4), makeMat('#fafaf9'));
    body.position.y = 1.5;
    body.castShadow = true;
    g.add(body);
    addWindows(g, 10, 3, 4, '#fafaf9');
    const awning = new THREE.Mesh(new THREE.BoxGeometry(10.5, 0.15, 1.5), makeMat('#d69e2e'));
    awning.position.set(0, 3, 2.5);
    awning.rotation.x = -0.1;
    g.add(awning);
    for (let x = -1; x <= 1; x += 2) {
        const col = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 3.2, 8), makeMat('#e8dcc8'));
        col.position.set(x * 1.5, 1.6, 2.1);
        g.add(col);
    }
    g.add(makeLabel(loc.nome, 5));
    return g;
}
function buildAllLocations() {
    LOCAIS.forEach(loc => {
        let building;
        const [px, , pz] = loc.pos;
        switch (loc.id) {
            case 'agora': building = buildAgora(loc); break;
            case 'torre_estrategia': building = buildTower(loc, '#4a90d9', 5, 5); break;
            case 'biblioteca': building = buildClassic(loc, '#92400e', 8, 5, 4); break;
            case 'cafe': building = buildCafe(loc); break;
            case 'arena': building = buildSemiCircle(loc, '#ef4444'); break;
            case 'jardim': building = buildGarden(loc); break;
            case 'tribunal': building = buildClassic(loc, '#94a3b8', 7, 5, 4); break;
            case 'laboratorio': building = buildModern(loc, '#2563eb', 6, 4, 3.5); break;
            case 'galeria': building = buildMuseum(loc); break;
            case 'sala_guerra': building = buildBunker(loc, '#374151'); break;
            case 'auditorio': building = buildDome(loc, '#b7791f', 5, 4); break;
            case 'atelie': building = buildColorfulStudio(loc); break;
            case 'observatorio': building = buildObservatory(loc); break;
            case 'res_norte': building = buildApartment(loc, '#64748b', 'modern'); break;
            case 'res_sul': building = buildApartment(loc, '#a16207', 'classic'); break;
            case 'res_leste': building = buildApartment(loc, '#15803d', 'zen'); break;
            case 'res_oeste': building = buildApartment(loc, '#1e293b', 'executive'); break;
            case 'refeitorio': building = buildRefeitorio(loc); break;
            case 'terraco': building = buildTerraco(loc); break;
            default: building = new THREE.Group(); break;
        }
        building.position.set(px, 0, pz);
        building.userData = { locId: loc.id, type: 'building' };
        scene.add(building);
        buildingGroups[loc.id] = building;
        building.traverse(child => {
            if (child.isMesh) {
                child.userData.locId = loc.id;
                child.userData.type = 'building';
                buildingMeshes.push(child);
            }
        });
    });
}
function buildPaths() {
    const pathMat = makeMat('#b8b0a0');
    const connections = [
        ['agora','torre_estrategia'],['agora','biblioteca'],['agora','cafe'],['agora','arena'],
        ['agora','auditorio'],['agora','refeitorio'],['agora','terraco'],['agora','jardim'],
        ['torre_estrategia','laboratorio'],['torre_estrategia','sala_guerra'],
        ['biblioteca','galeria'],['biblioteca','observatorio'],
        ['cafe','laboratorio'],['cafe','res_norte'],
        ['arena','tribunal'],['arena','res_sul'],
        ['jardim','atelie'],['jardim','res_leste'],['jardim','galeria'],
        ['sala_guerra','res_oeste'],['sala_guerra','auditorio'],
        ['auditorio','tribunal'],['auditorio','refeitorio'],
        ['res_norte','laboratorio'],['res_norte','observatorio'],
        ['res_sul','refeitorio'],['res_sul','tribunal'],
        ['refeitorio','terraco'],['terraco','atelie'],
        ['res_leste','atelie'],['res_oeste','torre_estrategia']
    ];
    connections.forEach(([a, b]) => {
        const la = LOCAIS.find(l => l.id === a);
        const lb = LOCAIS.find(l => l.id === b);
        if (!la || !lb) return;
        const dx = lb.pos[0] - la.pos[0];
        const dz = lb.pos[2] - la.pos[2];
        const len = Math.sqrt(dx * dx + dz * dz);
        const angle = Math.atan2(dx, dz);
        const path = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.05, len), pathMat);
        path.position.set(
            (la.pos[0] + lb.pos[0]) / 2,
            0.02,
            (la.pos[2] + lb.pos[2]) / 2
        );
        path.rotation.y = -angle;
        path.receiveShadow = true;
        scene.add(path);
    });
    const lightMat = makeMat('#fbbf24', { emissive: '#fbbf24', emissiveIntensity: 0.8 });
    connections.forEach(([a, b]) => {
        const la = LOCAIS.find(l => l.id === a);
        const lb = LOCAIS.find(l => l.id === b);
        if (!la || !lb) return;
        const dx = lb.pos[0] - la.pos[0];
        const dz = lb.pos[2] - la.pos[2];
        const len = Math.sqrt(dx * dx + dz * dz);
        const steps = Math.floor(len / 8);
        for (let i = 1; i < steps; i++) {
            const t = i / steps;
            const light = new THREE.Mesh(new THREE.SphereGeometry(0.12, 4, 4), lightMat);
            light.position.set(
                la.pos[0] + dx * t + 0.6,
                0.3,
                la.pos[2] + dz * t + 0.6
            );
            scene.add(light);
        }
    });
}
function buildEnvironment() {
    for (let i = 0; i < 45; i++) {
        const x = (Math.random() - 0.5) * 180, z = (Math.random() - 0.5) * 180;
        let ok = true;
        LOCAIS.forEach(l => { if (Math.sqrt((x-l.pos[0])**2+(z-l.pos[2])**2) < 10) ok = false; });
        if (ok) scene.add(makeTree(x, z, 0.6 + Math.random() * 0.6));
    }
    for (let i = 0; i < 25; i++) {
        const x = (Math.random() - 0.5) * 160, z = (Math.random() - 0.5) * 160;
        let ok = true;
        LOCAIS.forEach(l => { if (Math.sqrt((x-l.pos[0])**2+(z-l.pos[2])**2) < 8) ok = false; });
        if (ok) scene.add(makeBush(x, z, 0.5 + Math.random() * 0.5));
    }
}
const agentMeshes = [];
const agentLabels = [];
function createAgentMeshes() {
    AGENTES.forEach((agent, i) => {
        const cat = CATEGORIAS[agent.cat] || CATEGORIAS.omega;
        const isSpecial = agent.id === 'IGOR001' || agent.id === 'CL085';
        const radius = isSpecial ? 0.45 : 0.3;
        const g = new THREE.Group();
        const sphere = new THREE.Mesh(
            new THREE.SphereGeometry(radius, 12, 10),
            makeMat(cat.cor, { emissive: cat.cor, emissiveIntensity: 0.2 })
        );
        sphere.position.y = radius + 0.1;
        sphere.castShadow = true;
        g.add(sphere);
        if (isSpecial) {
            const ring = new THREE.Mesh(
                new THREE.TorusGeometry(radius + 0.08, 0.04, 6, 16),
                makeMat('#d69e2e', { emissive: '#d69e2e', emissiveIntensity: 0.5 })
            );
            ring.rotation.x = Math.PI / 2;
            ring.position.y = radius + 0.1;
            g.add(ring);
        }
        const lc = document.createElement('canvas');
        lc.width = 256; lc.height = 32;
        const lctx = lc.getContext('2d');
        lctx.fillStyle = 'rgba(15,23,42,0.8)';
        lctx.roundRect(0, 0, 256, 32, 6);
        lctx.fill();
        lctx.fillStyle = '#f8fafc';
        lctx.font = 'bold 16px Inter, sans-serif';
        lctx.textAlign = 'center';
        lctx.textBaseline = 'middle';
        const displayName = agent.nome.length > 16 ? agent.nome.substring(0, 14) + '..' : agent.nome;
        lctx.fillText(displayName, 128, 16);
        const ltex = new THREE.CanvasTexture(lc);
        const lmat = new THREE.SpriteMaterial({ map: ltex, transparent: true, depthWrite: false, opacity: 0 });
        const lsprite = new THREE.Sprite(lmat);
        lsprite.scale.set(3, 0.4, 1);
        lsprite.position.y = radius * 2 + 0.6;
        lsprite.renderOrder = 2;
        g.add(lsprite);
        agentLabels.push(lsprite);
        const loc = LOCAIS.find(l => l.id === agent.local);
        if (loc) {
            const angle = (i / AGENTES.length) * Math.PI * 2;
            const dist = 2 + Math.random() * 3;
            g.position.set(
                loc.pos[0] + Math.cos(angle) * dist,
                0,
                loc.pos[2] + Math.sin(angle) * dist
            );
        }
        g.userData = { agentId: agent.id, type: 'agent', index: i };
        sphere.userData = { agentId: agent.id, type: 'agent', index: i };
        buildingMeshes.push(sphere); 
        scene.add(g);
        agentMeshes.push(g);
        agent._mesh = g;
        agent._startPos = g.position.clone();
        agent._targetPos = g.position.clone();
        agent._moveTime = 0;
        agent._moveDuration = 0;
    });
}
const fountainParticles = [];
function createFountainParticles() {
    const particleCount = 50;
    const pMat = makeMat('#60a5fa', { transparent: true, opacity: 0.6 });
    for (let i = 0; i < particleCount; i++) {
        const p = new THREE.Mesh(new THREE.SphereGeometry(0.06, 4, 4), pMat);
        p.position.set(0, 1.2, 0); 
        p.userData = {
            vx: (Math.random() - 0.5) * 0.04,
            vy: 0.05 + Math.random() * 0.06,
            vz: (Math.random() - 0.5) * 0.04,
            life: Math.random()
        };
        scene.add(p);
        fountainParticles.push(p);
    }
}
let simTime = 8 * 60; 
let simDay = 1;
let paused = false;
let isNight = false; // FIXO: sempre dia (ciclo dia/noite removido)
let selectedBuilding = null;
let selectedAgent = null;
let helpVisible = false;
function buildLeftPanel() {
    const panel = document.getElementById('leftPanel');
    const grupos = {
        publico: { nome: 'Espacos Publicos', items: [] },
        trabalho: { nome: 'Trabalho e Pesquisa', items: [] },
        lazer: { nome: 'Lazer e Cultura', items: [] },
        residencia: { nome: 'Residencias', items: [] },
        especial: { nome: 'Especiais', items: [] }
    };
    LOCAIS.forEach(l => { if (grupos[l.grupo]) grupos[l.grupo].items.push(l); });
    let html = '<div class="panel-header"><h3>Locais do Campus</h3></div>';
    Object.entries(grupos).forEach(([key, grupo]) => {
        html += `<div class="section-title">${grupo.nome}</div>`;
        grupo.items.forEach(loc => {
            const count = AGENTES.filter(a => a.local === loc.id).length;
            html += `<div class="loc-item" data-loc="${loc.id}" onclick="flyToBuilding('${loc.id}')">
                <div class="loc-icon" style="background:${loc.cor}20;color:${loc.cor}">${loc.icone}</div>
                <div class="loc-info">
                    <div class="loc-name">${loc.nome}</div>
                    <div class="loc-type">${loc.tipo}</div>
                </div>
                <div class="loc-badge" id="badge-${loc.id}">${count}</div>
            </div>`;
        });
    });
    panel.innerHTML = html;
}
function updateBadges() {
    LOCAIS.forEach(loc => {
        const count = AGENTES.filter(a => a.local === loc.id).length;
        const badge = document.getElementById('badge-' + loc.id);
        if (badge) badge.textContent = count;
    });
    document.getElementById('agentCount').textContent = AGENTES.length;
}
function showBuildingInfo(locId) {
    const loc = LOCAIS.find(l => l.id === locId);
    if (!loc) return;
    selectedBuilding = locId;
    const agentsHere = AGENTES.filter(a => a.local === locId);
    const occ = Math.round((agentsHere.length / loc.cap) * 100);
    document.getElementById('buildingInfo').innerHTML = `
        <h2>${loc.nome}</h2>
        <div class="building-type">${loc.icone} ${loc.tipo}</div>
        <div class="building-desc">${loc.desc}</div>
        <div class="occupancy">
            <div class="occ-bar"><div class="occ-fill" style="width:${Math.min(occ, 100)}%"></div></div>
            <div class="occ-label">${agentsHere.length}/${loc.cap} ocupacao (${occ}%)</div>
        </div>
    `;
    const listEl = document.getElementById('agentsAtBuilding');
    listEl.innerHTML = agentsHere.map(a => {
        const cat = CATEGORIAS[a.cat] || CATEGORIAS.omega;
        return `<div class="agent-chip" onclick="showAgentPanel('${a.id}')">
            <div class="chip-dot" style="background:${cat.cor}"></div>
            <span class="chip-name">${a.nome}</span>
            <span class="chip-tier">${a.tier}</span>
        </div>`;
    }).join('');
    document.getElementById('bottomBar').classList.add('visible');
    document.querySelectorAll('.loc-item').forEach(el => el.classList.remove('active'));
    const locEl = document.querySelector(`.loc-item[data-loc="${locId}"]`);
    if (locEl) locEl.classList.add('active');
}
function closeBottomBar() {
    document.getElementById('bottomBar').classList.remove('visible');
    selectedBuilding = null;
    document.querySelectorAll('.loc-item').forEach(el => el.classList.remove('active'));
}
function showAgentPanel(agentId) {
    const agent = AGENTES.find(a => a.id === agentId);
    if (!agent) return;
    selectedAgent = agentId;
    const cat = CATEGORIAS[agent.cat] || CATEGORIAS.omega;
    const loc = LOCAIS.find(l => l.id === agent.local);
    document.getElementById('agentPanelContent').innerHTML = `
        <div class="ap-avatar" style="background:${cat.bg};border-color:${cat.cor};color:${cat.cor}">${agent.nome.charAt(0)}</div>
        <div class="ap-name">${agent.nome}</div>
        <div class="ap-title">${agent.titulo}</div>
        <div class="ap-badges">
            <span class="ap-badge" style="background:${cat.bg};color:${cat.cor}">${cat.nome}</span>
            <span class="ap-badge" style="background:rgba(214,158,46,0.15);color:#d69e2e">Tier ${agent.tier}</span>
        </div>
        <div class="ap-section">
            <div class="ap-section-title">Localizacao Atual</div>
            <div class="ap-section-value">${loc ? loc.nome : 'Em transito'}</div>
        </div>
        <div class="ap-section">
            <div class="ap-section-title">Atividade</div>
            <div class="ap-section-value">${getActivity(agent)}</div>
        </div>
        <div class="ap-section">
            <div class="ap-section-title">ID</div>
            <div class="ap-section-value" style="font-family:monospace;font-size:11px;color:#64748b">${agent.id}</div>
        </div>
        <a href="rede.html" class="ap-link">Ver Perfil Completo</a>
    `;
    document.getElementById('agentPanel').classList.add('visible');
}
function closeAgentPanel() {
    document.getElementById('agentPanel').classList.remove('visible');
    selectedAgent = null;
}
function getActivity(agent) {
    const loc = LOCAIS.find(l => l.id === agent.local);
    if (!loc) return 'Caminhando...';
    const activities = {
        agora: ['Debatendo no anfiteatro', 'Ouvindo apresentacao', 'Mediando discussao'],
        torre_estrategia: ['Planejando cenarios', 'Analisando dados', 'Em reuniao estrategica'],
        biblioteca: ['Pesquisando referencias', 'Lendo tratado', 'Catalogando insights'],
        cafe: ['Tomando cafe', 'Conversando informalmente', 'Redigindo notas'],
        arena: ['Debatendo posicoes', 'Assistindo simulacao', 'Preparando argumentos'],
        jardim: ['Meditando', 'Contemplando ideias', 'Passeando pelo jardim'],
        tribunal: ['Avaliando argumentos', 'Julgando proposta', 'Revisando logica'],
        laboratorio: ['Prototipando conceito', 'Testando hipotese', 'Experimentando modelo'],
        galeria: ['Visitando exposicao', 'Analisando legados', 'Refletindo sobre historia'],
        sala_guerra: ['Operacao tatica', 'Monitorando cenario', 'Planejando movimento'],
        auditorio: ['Assistindo palestra', 'Apresentando keynote', 'Participando de painel'],
        atelie: ['Criando prototipo', 'Design thinking', 'Brainstorming visual'],
        observatorio: ['Analisando tendencias', 'Prospectando futuro', 'Calibrando modelos'],
        res_norte: ['Descansando', 'Trabalhando remotamente', 'Lendo artigos'],
        res_sul: ['Relaxando', 'Praticando hobby', 'Escrevendo diario'],
        res_leste: ['Meditando', 'Fazendo yoga', 'Cultivando jardim zen'],
        res_oeste: ['No escritorio privado', 'Videoconferencia', 'Organizando agenda'],
        refeitorio: ['Almocando', 'Socializando no jantar', 'Provando gastronomia'],
        terraco: ['Apreciando a vista', 'Networking', 'Foto panoramica']
    };
    const acts = activities[loc.id] || ['Explorando o campus'];
    return acts[Math.floor(Math.random() * acts.length)];
}
function flyToBuilding(locId) {
    const loc = LOCAIS.find(l => l.id === locId);
    if (!loc) return;
    showBuildingInfo(locId);
    const target = new THREE.Vector3(loc.pos[0], 2, loc.pos[2]);
    const camTarget = new THREE.Vector3(
        loc.pos[0] + 20,
        18,
        loc.pos[2] + 20
    );
    animateCamera(camTarget, target);
}
let cameraAnimating = false;
let cameraAnimStart, cameraAnimDuration = 1.5;
let camFrom, camTo, targetFrom, targetTo;
function animateCamera(newPos, newTarget) {
    camFrom = camera.position.clone();
    camTo = newPos.clone();
    targetFrom = controls.target.clone();
    targetTo = newTarget.clone();
    cameraAnimStart = performance.now() / 1000;
    cameraAnimating = true;
}
function resetCamera() {
    animateCamera(new THREE.Vector3(70, 65, 70), new THREE.Vector3(0, 0, 0));
}
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
let hoveredObject = null;
canvas.addEventListener('mousemove', (e) => {
    mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(buildingMeshes);
    const tooltip = document.getElementById('tooltip3d');
    if (intersects.length > 0) {
        const obj = intersects[0].object;
        canvas.style.cursor = 'pointer';
        if (obj.userData.type === 'building') {
            const loc = LOCAIS.find(l => l.id === obj.userData.locId);
            if (loc) {
                document.getElementById('ttName').textContent = loc.nome;
                document.getElementById('ttSub').textContent = loc.tipo + ' — ' + AGENTES.filter(a => a.local === loc.id).length + ' agentes';
                tooltip.style.display = 'block';
                tooltip.style.left = e.clientX + 'px';
                tooltip.style.top = e.clientY + 'px';
            }
        } else if (obj.userData.type === 'agent') {
            const agent = AGENTES[obj.userData.index];
            if (agent) {
                document.getElementById('ttName').textContent = agent.nome;
                const cat = CATEGORIAS[agent.cat] || CATEGORIAS.omega;
                document.getElementById('ttSub').textContent = cat.nome + ' — Tier ' + agent.tier;
                tooltip.style.display = 'block';
                tooltip.style.left = e.clientX + 'px';
                tooltip.style.top = e.clientY + 'px';
            }
        }
        hoveredObject = obj;
    } else {
        canvas.style.cursor = 'default';
        tooltip.style.display = 'none';
        hoveredObject = null;
    }
});
canvas.addEventListener('click', (e) => {
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(buildingMeshes);
    if (intersects.length > 0) {
        const obj = intersects[0].object;
        if (obj.userData.type === 'building') {
            showBuildingInfo(obj.userData.locId);
        } else if (obj.userData.type === 'agent') {
            const agent = AGENTES[obj.userData.index];
            if (agent) showAgentPanel(agent.id);
        }
    }
});
canvas.addEventListener('dblclick', (e) => {
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(buildingMeshes);
    if (intersects.length > 0) {
        const obj = intersects[0].object;
        if (obj.userData.type === 'building') {
            flyToBuilding(obj.userData.locId);
        } else if (obj.userData.type === 'agent') {
            const agent = AGENTES[obj.userData.index];
            if (agent) flyToBuilding(agent.local);
        }
    }
});
const keys = {};
document.addEventListener('keydown', (e) => {
    keys[e.key.toLowerCase()] = true;
    if (e.key === ' ' || e.code === 'Space') {
        e.preventDefault();
        paused = !paused;
        document.getElementById('pauseIndicator').classList.toggle('visible', paused);
    }
    if (e.key.toLowerCase() === 'r') resetCamera();
    if (e.key.toLowerCase() === 'h') toggleHelp();
    // tecla 'n' dia/noite removida
    if (e.key === 'Escape') {
        closeBottomBar();
        closeAgentPanel();
    }
});
document.addEventListener('keyup', (e) => { keys[e.key.toLowerCase()] = false; });
function handleKeyMovement() {
    const speed = 0.5;
    const forward = new THREE.Vector3();
    camera.getWorldDirection(forward);
    forward.y = 0;
    forward.normalize();
    const right = new THREE.Vector3().crossVectors(forward, new THREE.Vector3(0, 1, 0)).normalize();
    if (keys['w']) { controls.target.add(forward.clone().multiplyScalar(speed)); camera.position.add(forward.clone().multiplyScalar(speed)); }
    if (keys['s']) { controls.target.add(forward.clone().multiplyScalar(-speed)); camera.position.add(forward.clone().multiplyScalar(-speed)); }
    if (keys['a']) { controls.target.add(right.clone().multiplyScalar(-speed)); camera.position.add(right.clone().multiplyScalar(-speed)); }
    if (keys['d']) { controls.target.add(right.clone().multiplyScalar(speed)); camera.position.add(right.clone().multiplyScalar(speed)); }
}
// toggleDayNight() removida — cenario sempre em modo DIA
function toggleDayNight() { /* desabilitada */ }
function togglePanel() {
    const panel = document.getElementById('leftPanel');
    const toggle = document.getElementById('panelToggle');
    panel.classList.toggle('collapsed');
    toggle.classList.toggle('collapsed');
    toggle.innerHTML = panel.classList.contains('collapsed') ? '&#9654;' : '&#9664;';
}
function toggleHelp() {
    helpVisible = !helpVisible;
    document.getElementById('helpOverlay').classList.toggle('visible', helpVisible);
}
let lastMoveTime = 0;
const MOVE_INTERVAL = 3; 
function simulateAgentMovement(time) {
    if (paused) return;
    if (time - lastMoveTime > MOVE_INTERVAL) {
        lastMoveTime = time;
        const numToMove = 5 + Math.floor(Math.random() * 6);
        for (let i = 0; i < numToMove; i++) {
            const agent = AGENTES[Math.floor(Math.random() * AGENTES.length)];
            if (agent.moving) continue;
            const newLoc = LOCAIS[Math.floor(Math.random() * LOCAIS.length)];
            if (newLoc.id === agent.local) continue;
            agent.targetLocal = newLoc.id;
            agent.moving = true;
            const targetAngle = Math.random() * Math.PI * 2;
            const targetDist = 2 + Math.random() * 3;
            agent._startPos = agent._mesh.position.clone();
            agent._targetPos = new THREE.Vector3(
                newLoc.pos[0] + Math.cos(targetAngle) * targetDist,
                0,
                newLoc.pos[2] + Math.sin(targetAngle) * targetDist
            );
            agent._moveTime = time;
            agent._moveDuration = 2 + Math.random() * 3;
        }
    }
    AGENTES.forEach(agent => {
        if (!agent.moving || !agent._mesh) return;
        const elapsed = time - agent._moveTime;
        const t = Math.min(elapsed / agent._moveDuration, 1);
        const eased = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
        agent._mesh.position.lerpVectors(agent._startPos, agent._targetPos, eased);
        agent._mesh.position.y = Math.sin(t * Math.PI) * 0.3;
        if (t >= 1) {
            agent.moving = false;
            agent.local = agent.targetLocal;
            agent._mesh.position.y = 0;
        }
    });
}
let clock = new THREE.Clock();
function updateSimTime(dt) {
    if (paused) return;
    simTime += dt * 10; // 10x speed: 1 real second = 10 sim minutes
    if (simTime >= 24 * 60) {
        simTime -= 24 * 60;
        simDay++;
        document.getElementById('dayCount').textContent = simDay;
    }
    const hours = Math.floor(simTime / 60);
    const mins = Math.floor(simTime % 60);
    document.getElementById('clockDisplay').textContent =
        String(hours).padStart(2, '0') + ':' + String(mins).padStart(2, '0');
}
function animateFountain(time) {
    fountainParticles.forEach(p => {
        p.userData.life += 0.02;
        if (p.userData.life > 1) {
            p.userData.life = 0;
            p.position.set(0, 1.2, 0);
            p.userData.vx = (Math.random() - 0.5) * 0.04;
            p.userData.vy = 0.05 + Math.random() * 0.06;
            p.userData.vz = (Math.random() - 0.5) * 0.04;
        }
        p.position.x += p.userData.vx;
        p.position.y += p.userData.vy;
        p.position.z += p.userData.vz;
        p.userData.vy -= 0.002; 
        p.material.opacity = 1 - p.userData.life;
    });
}
function animateTreeSway(time) {
    scene.traverse(child => {
        if (child.isMesh && child.geometry.type === 'ConeGeometry') {
            child.rotation.z = Math.sin(time * 0.5 + child.position.x * 0.1) * 0.02;
            child.rotation.x = Math.cos(time * 0.3 + child.position.z * 0.1) * 0.015;
        }
    });
}
function updateAgentLabelVisibility() {
    const camPos = camera.position;
    agentMeshes.forEach((mesh, i) => {
        const label = agentLabels[i];
        if (!label) return;
        const dist = camPos.distanceTo(mesh.position);
        const agent = AGENTES[i];
        const isHovered = hoveredObject && hoveredObject.userData.agentId === agent.id;
        const targetOpacity = (dist < 30 || isHovered) ? 1 : 0;
        label.material.opacity += (targetOpacity - label.material.opacity) * 0.1;
    });
}
function animate() {
    requestAnimationFrame(animate);
    const dt = clock.getDelta();
    const time = clock.getElapsedTime();
    if (cameraAnimating) {
        const elapsed = performance.now() / 1000 - cameraAnimStart;
        const t = Math.min(elapsed / cameraAnimDuration, 1);
        const eased = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
        camera.position.lerpVectors(camFrom, camTo, eased);
        controls.target.lerpVectors(targetFrom, targetTo, eased);
        if (t >= 1) cameraAnimating = false;
    }
    handleKeyMovement();
    controls.update();
    updateSimTime(dt);
    simulateAgentMovement(time);
    animateFountain(time);
    animateTreeSway(time);
    updateAgentLabelVisibility();
    if (selectedBuilding && buildingGroups[selectedBuilding]) {
        const bGroup = buildingGroups[selectedBuilding];
        bGroup.traverse(child => {
            if (child.isMesh && child.material && child.material.emissive) {
                child.material.emissiveIntensity = 0.1 + Math.sin(time * 3) * 0.05;
            }
        });
    }
    if (selectedBuilding) {
        updateBadges();
    }
    renderer.render(scene, camera);
}
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});
function init() {
    const loadFill = document.getElementById('loadingFill');
    loadFill.style.width = '20%';
    setTimeout(() => {
        buildAllLocations();
        loadFill.style.width = '40%';
        setTimeout(() => {
            buildPaths();
            buildEnvironment();
            loadFill.style.width = '60%';
            setTimeout(() => {
                createAgentMeshes();
                createFountainParticles();
                loadFill.style.width = '80%';
                setTimeout(() => {
                    buildLeftPanel();
                    updateBadges();
                    loadFill.style.width = '100%';
                    setTimeout(() => {
                        document.getElementById('loadingScreen').classList.add('done');
                        animate();
                    }, 500);
                }, 100);
            }, 100);
        }, 100);
    }, 200);
}
init();
